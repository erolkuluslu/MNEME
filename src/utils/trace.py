"""
MNEME Query Trace Utilities

Functions to format and display query execution traces showing:
- Query analysis and planning
- Retrieval strategy and scoring
- Thinking engine decisions
- Citation generation with match indicators
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.query import QueryPlan
    from src.models.retrieval import RetrievalResult, ScoredChunk
    from src.models.answer import EnhancedAnswer, Citation


def format_query_plan(plan: "QueryPlan") -> str:
    """
    Format query analysis/planning phase as displayable trace.

    Args:
        plan: QueryPlan from query analyzer

    Returns:
        Formatted string showing query analysis
    """
    lines = [
        "📊 Query Analysis:",
        f"   Type: {plan.query_type.value}",
        f"   Intent: {plan.intent.value}",
        f"   Year Filter: {plan.year_filter or 'None'}",
        f"   Category Filter: {plan.category_filter or 'None'}",
    ]

    if plan.expansion.expanded_terms:
        terms = ", ".join(plan.expansion.expanded_terms[:5])
        lines.append(f"   Expanded Terms: [{terms}]")

    if plan.expansion.related_concepts:
        concepts = ", ".join(plan.expansion.related_concepts[:5])
        lines.append(f"   Related Concepts: [{concepts}]")

    if plan.filters.year_expansion:
        years = ", ".join(str(y) for y in plan.filters.year_expansion)
        lines.append(f"   Year Expansion: [{years}]")

    lines.extend([
        f"   Strategy: {plan.retrieval_strategy}",
        f"   Target Docs: {plan.min_docs}-{plan.max_docs}",
    ])

    if plan.classification_confidence > 0:
        lines.append(f"   Classification Confidence: {plan.classification_confidence:.2f}")

    return "\n".join(lines)


def format_retrieval_trace(result: "RetrievalResult", max_candidates: int = 5) -> str:
    """
    Format retrieval execution trace showing scoring breakdown.

    Args:
        result: RetrievalResult from retrieval engine
        max_candidates: Maximum candidates to show in detail

    Returns:
        Formatted string showing retrieval trace
    """
    lines = [
        "🔍 Retrieval Trace:",
        f"   Strategy: {result.retrieval_strategy}",
        f"   Candidates Considered: {result.total_candidates_considered} → Final: {len(result.candidates)}",
    ]

    if result.year_filter:
        lines.append(f"   Year Filter: {result.year_filter} (matched: {result.num_year_matched}/{len(result.candidates)})")

    if result.category_filter:
        lines.append(f"   Category Filter: {result.category_filter} (matched: {result.num_category_matched}/{len(result.candidates)})")

    lines.extend([
        f"   Confidence: {result.confidence.value}",
        f"   Retrieval Time: {result.retrieval_time_ms:.1f}ms",
        "",
        "   Scoring Breakdown:",
    ])

    for i, sc in enumerate(result.candidates[:max_candidates], 1):
        year_mark = "✓" if sc.year_matched else " "
        cat_mark = "✓" if sc.category_matched else " "

        # Build score components
        scores_parts = []
        if sc.vector_score > 0:
            scores_parts.append(f"Vec:{sc.vector_score:.2f}")
        if sc.bm25_score > 0:
            scores_parts.append(f"BM25:{sc.bm25_score:.2f}")
        if sc.combined_score > 0:
            scores_parts.append(f"RRF:{sc.combined_score:.2f}")

        # Build boost info
        boosts = []
        if sc.year_boost > 0:
            boosts.append(f"+Year:{sc.year_boost:.2f}")
        if sc.category_boost > 0:
            boosts.append(f"+Cat:{sc.category_boost:.2f}")

        boost_str = " ".join(boosts) if boosts else ""

        lines.append(f"   [{i}] {sc.chunk_id} | {sc.category}/{sc.year} {year_mark}{cat_mark}")

        score_line = " | ".join(scores_parts)
        if boost_str:
            score_line += f" {boost_str}"
        score_line += f" → Final:{sc.final_score:.2f}"
        lines.append(f"       {score_line}")

    if len(result.candidates) > max_candidates:
        lines.append(f"   ... and {len(result.candidates) - max_candidates} more candidates")

    return "\n".join(lines)


def format_thinking_trace(
    coverage_gaps: List[str],
    missing_years: List[int],
    retrieval_result: "RetrievalResult"
) -> str:
    """
    Format thinking engine trace showing gap detection and context building.

    Args:
        coverage_gaps: List of detected coverage gaps
        missing_years: List of years not covered
        retrieval_result: The retrieval result analyzed

    Returns:
        Formatted string showing thinking trace
    """
    lines = [
        "🧠 Thinking Trace:",
        f"   Sources Retrieved: {len(retrieval_result.candidates)}",
        f"   Years Represented: {retrieval_result.years_represented}",
        f"   Categories Represented: {retrieval_result.categories_represented}",
    ]

    if coverage_gaps:
        lines.append("")
        lines.append("   Coverage Gaps Detected:")
        for gap in coverage_gaps[:3]:
            lines.append(f"     ⚠️ {gap}")

    if missing_years:
        lines.append(f"   Missing Years: {missing_years}")

    if not coverage_gaps and not missing_years:
        lines.append("   ✅ No coverage gaps detected")

    return "\n".join(lines)


def format_citations(
    citations: List["Citation"],
    year_filter: Optional[int] = None,
    max_citations: int = 10
) -> str:
    """
    Format citations with year match indicators.

    Args:
        citations: List of Citation objects
        year_filter: Year filter that was applied (if any)
        max_citations: Maximum citations to display

    Returns:
        Formatted string showing citations
    """
    if not citations:
        return "📚 Citations: None"

    lines = ["📚 Citations:"]

    for citation in citations[:max_citations]:
        year_mark = "✓" if citation.year_matched else " "
        score_str = f" (score: {citation.relevance_score:.2f})" if citation.relevance_score > 0 else ""

        lines.append(f"   [{citation.index}] {year_mark} {citation.category}/{citation.year} - {citation.title or citation.doc_id}{score_str}")

        if citation.excerpt:
            excerpt = citation.excerpt[:80] + "..." if len(citation.excerpt) > 80 else citation.excerpt
            lines.append(f"       \"{excerpt}\"")

    if len(citations) > max_citations:
        lines.append(f"   ... and {len(citations) - max_citations} more sources")

    return "\n".join(lines)


def format_full_trace(
    plan: "QueryPlan",
    retrieval_result: "RetrievalResult",
    answer: "EnhancedAnswer"
) -> str:
    """
    Format complete query execution trace.

    Args:
        plan: QueryPlan from analyzer
        retrieval_result: RetrievalResult from retrieval
        answer: EnhancedAnswer from generation

    Returns:
        Complete formatted trace
    """
    sections = [
        format_query_plan(plan),
        "",
        format_retrieval_trace(retrieval_result),
        "",
        format_thinking_trace(
            coverage_gaps=answer.coverage_gaps,
            missing_years=retrieval_result.missing_years,
            retrieval_result=retrieval_result
        ),
    ]

    return "\n".join(sections)


def format_answer_with_trace(
    answer: "EnhancedAnswer",
    show_full_trace: bool = False,
    plan: Optional["QueryPlan"] = None,
    retrieval_result: Optional["RetrievalResult"] = None
) -> str:
    """
    Format answer with optional trace information.

    Args:
        answer: EnhancedAnswer to display
        show_full_trace: Whether to show full trace
        plan: QueryPlan (required if show_full_trace)
        retrieval_result: RetrievalResult (required if show_full_trace)

    Returns:
        Formatted answer with trace
    """
    lines = []

    # Show trace if requested and available
    if show_full_trace and plan and retrieval_result:
        lines.append(format_full_trace(plan, retrieval_result, answer))
        lines.append("")

    # Confidence indicator
    confidence_emoji = {
        "year_matched": "📈",
        "good_match": "👍",
        "partial_match": "⚠️",
        "low_match": "👎",
        "no_results": "❌",
    }
    conf_icon = confidence_emoji.get(answer.confidence, "📊")
    lines.append(f"{conf_icon} Confidence: {answer.confidence}")
    lines.append("")

    # Answer
    lines.append("💬 ANSWER:")
    lines.append("-" * 60)
    lines.append(answer.answer)
    lines.append("-" * 60)

    # Citations
    lines.append("")
    lines.append(format_citations(answer.citations, answer.year_filter))

    # Coverage gaps if any
    if answer.coverage_gaps:
        lines.append("")
        lines.append("⚠️  Coverage Gaps:")
        for gap in answer.coverage_gaps:
            lines.append(f"   - {gap}")

    # Stats
    lines.extend([
        "",
        f"📊 Stats: {answer.latency_ms:.0f}ms | {answer.num_sources_used} sources | {len(answer.citations)} citations",
    ])

    return "\n".join(lines)
