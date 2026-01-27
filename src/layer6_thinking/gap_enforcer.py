"""
Gap Enforcer Module

Manages gap detection and iterative retrieval triggering (IRCoT-style).
"""

import re
from typing import List, Dict, Any, Optional
import logging

from src.models.retrieval import RetrievalResult
from src.config import MNEMEConfig

logger = logging.getLogger(__name__)


class GapEnforcer:
    """
    Enforces gap detection and manages iterative retrieval.

    Analyzes coverage gaps from retrieval results and determines
    whether to warn users or trigger iterative retrieval.
    """

    # Patterns for critical gap detection
    CRITICAL_GAP_PATTERNS = [
        r"No documents from (\d{4}) matched",
        r"No documents from category .+ found",
        r"Missing years?: \[.+\]",
        r"No .+ documents found",
    ]

    # Patterns for minor/synthesis gaps
    MINOR_GAP_PATTERNS = [
        r"Limited coverage",
        r"Partial match",
    ]

    # Severity levels
    SEVERITY_CRITICAL = "critical"
    SEVERITY_HIGH = "high"
    SEVERITY_SIGNIFICANT = "significant"
    SEVERITY_MINOR = "minor"
    SEVERITY_LOW = "low"

    def should_warn_about_gaps(self, gaps: List[str]) -> bool:
        """
        Determine if gaps warrant user warning.

        Args:
            gaps: List of gap descriptions

        Returns:
            True if gaps are significant enough to warn user
        """
        if not gaps:
            return False

        # Check for critical gaps
        for gap in gaps:
            for pattern in self.CRITICAL_GAP_PATTERNS:
                if re.search(pattern, gap, re.IGNORECASE):
                    logger.debug(f"Critical gap detected: {gap}")
                    return True

        return False

    def get_gap_warning_prompt(self, gaps: List[str]) -> str:
        """
        Generate warning prompt text for gaps.

        Args:
            gaps: List of gap descriptions

        Returns:
            Warning prompt string to include in LLM context
        """
        if not gaps:
            return ""

        # Build warning prompt
        warning_parts = [
            "NOTE: The following information gaps were detected in the retrieved sources:"
        ]

        for gap in gaps:
            # Extract key information from gap
            year_match = re.search(r"(\d{4})", gap)
            category_match = re.search(r"category ['\"]?([^'\"]+)['\"]?", gap, re.IGNORECASE)

            if year_match:
                warning_parts.append(f"- Year {year_match.group(1)} may have limited coverage")
            elif category_match:
                warning_parts.append(f"- Category '{category_match.group(1)}' may have limited coverage")
            else:
                warning_parts.append(f"- {gap}")

        warning_parts.append(
            "Please acknowledge these limitations in your response if relevant."
        )

        return "\n".join(warning_parts)

    def should_trigger_iterative_retrieval(
        self,
        gaps: List[str],
        config: MNEMEConfig,
    ) -> bool:
        """
        Determine if iterative retrieval should be triggered.

        IRCoT-style: trigger when significant gaps detected and enabled.

        Args:
            gaps: List of gap descriptions
            config: MNEME configuration

        Returns:
            True if iterative retrieval should be triggered
        """
        # Check if iterative retrieval is enabled
        if not config.enable_iterative_retrieval:
            return False

        # No gaps = no iterative retrieval needed
        if not gaps:
            return False

        # Count significant gaps
        significant_gap_count = 0
        for gap in gaps:
            severity = self.classify_gap_severity(gap)
            if severity in [self.SEVERITY_CRITICAL, self.SEVERITY_HIGH, self.SEVERITY_SIGNIFICANT]:
                significant_gap_count += 1

        # Trigger if multiple significant gaps or any critical gap
        for gap in gaps:
            severity = self.classify_gap_severity(gap)
            if severity == self.SEVERITY_CRITICAL:
                logger.info(f"Iterative retrieval triggered by critical gap: {gap}")
                return True

        if significant_gap_count >= 2:
            logger.info(
                f"Iterative retrieval triggered by {significant_gap_count} significant gaps"
            )
            return True

        return False

    def classify_gap_severity(self, gap: str) -> str:
        """
        Classify the severity of a gap.

        Args:
            gap: Gap description string

        Returns:
            Severity level string
        """
        gap_lower = gap.lower()

        # Critical gaps
        if re.search(r"no documents from \d{4} matched", gap_lower):
            return self.SEVERITY_CRITICAL
        if "missing years" in gap_lower and len(re.findall(r"\d{4}", gap)) >= 2:
            return self.SEVERITY_CRITICAL

        # High severity gaps
        if re.search(r"no documents from category", gap_lower):
            return self.SEVERITY_HIGH
        if "missing year" in gap_lower:
            return self.SEVERITY_HIGH

        # Significant gaps
        if "missing category" in gap_lower or "missing categories" in gap_lower:
            return self.SEVERITY_SIGNIFICANT

        # Minor gaps
        for pattern in self.MINOR_GAP_PATTERNS:
            if re.search(pattern, gap_lower):
                return self.SEVERITY_MINOR

        return self.SEVERITY_LOW

    def analyze_result(self, result: RetrievalResult) -> Dict[str, Any]:
        """
        Analyze retrieval result for gaps.

        Args:
            result: Retrieval result to analyze

        Returns:
            Analysis dictionary with gap information
        """
        gaps = result.coverage_gaps or []
        missing_years = result.missing_years or []

        # Classify all gaps
        gap_severities = {}
        for gap in gaps:
            gap_severities[gap] = self.classify_gap_severity(gap)

        # Determine if there are critical gaps
        has_critical = any(
            s in [self.SEVERITY_CRITICAL, self.SEVERITY_HIGH]
            for s in gap_severities.values()
        )

        return {
            "has_critical_gaps": has_critical,
            "gaps": gaps,
            "gap_severities": gap_severities,
            "missing_years": missing_years,
            "gap_summary": self._generate_gap_summary(gaps, gap_severities),
        }

    def _generate_gap_summary(
        self,
        gaps: List[str],
        severities: Dict[str, str],
    ) -> str:
        """Generate a summary of gaps."""
        if not gaps:
            return "No coverage gaps detected."

        critical_count = sum(1 for s in severities.values() if s == self.SEVERITY_CRITICAL)
        high_count = sum(1 for s in severities.values() if s == self.SEVERITY_HIGH)

        parts = []
        if critical_count > 0:
            parts.append(f"{critical_count} critical gap(s)")
        if high_count > 0:
            parts.append(f"{high_count} high-severity gap(s)")

        if parts:
            return f"Detected: {', '.join(parts)}"
        return f"Detected {len(gaps)} minor gap(s)"

    def get_iterative_suggestions(self, result: RetrievalResult) -> List[str]:
        """
        Get suggestions for iterative retrieval.

        Args:
            result: Retrieval result

        Returns:
            List of suggestions for improving retrieval
        """
        suggestions = []

        if result.missing_years:
            if len(result.missing_years) > 1:
                suggestions.append(
                    f"Expand year range to include {result.missing_years}"
                )
            else:
                suggestions.append(
                    f"Try adjacent years to {result.missing_years[0]}"
                )

        if result.year_filter and result.num_year_matched == 0:
            suggestions.append(
                "Relax year filter or expand year range"
            )

        if not suggestions:
            suggestions.append("Try broadening search terms")

        return suggestions


def create_gap_enforcer() -> GapEnforcer:
    """Factory function to create gap enforcer."""
    return GapEnforcer()
