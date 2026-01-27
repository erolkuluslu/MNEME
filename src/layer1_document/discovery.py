"""
Document Discovery Module

Handles document discovery from directories with various file formats.
"""

import os
import glob
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
import re

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredDocument:
    """A discovered document with its content and metadata."""

    doc_id: str
    content: str
    file_path: str
    file_name: str

    # Extracted metadata
    year: int
    category: str

    # File metadata
    file_size: int = 0
    file_extension: str = ""
    word_count: int = 0

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentDiscovery:
    """
    Discovers and loads documents from a directory structure.

    Supports multiple file formats and extracts metadata from
    file names and directory structure.
    """

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".pdf"}

    # Pattern to extract year from filename (e.g., "paper_2020.txt")
    YEAR_PATTERNS = [
        r"[_-](\d{4})[_.-]",  # paper_2020.txt
        r"(\d{4})[_-]",  # 2020_paper.txt
        r"[_-](\d{4})$",  # paper_2020 (at end)
        r"^(\d{4})[_-]",  # 2020-paper
        r"\((\d{4})\)",  # paper (2020).txt
    ]

    # Ignore patterns
    IGNORE_PATTERNS = ["README.md"]

    def __init__(
        self,
        base_path: str,
        supported_extensions: Optional[set] = None,
        category_from_folder: bool = True,
        default_year: int = 2020,
        default_category: str = "general",
        year_extractor: Optional[Callable[[str], Optional[int]]] = None,
        category_extractor: Optional[Callable[[str], Optional[str]]] = None,
        year_patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize document discovery.

        Args:
            base_path: Base directory to search
            supported_extensions: Set of supported file extensions
            category_from_folder: Extract category from parent folder name
            default_year: Default year if not extractable
            default_category: Default category if not extractable
            year_extractor: Custom function to extract year from path
            category_extractor: Custom function to extract category from path
            year_patterns: Custom regex patterns for year extraction
        """
        self.base_path = Path(base_path)
        self.supported_extensions = supported_extensions or self.SUPPORTED_EXTENSIONS
        self.category_from_folder = category_from_folder
        self.default_year = default_year
        self.default_category = default_category
        self.year_extractor = year_extractor
        self.category_extractor = category_extractor
        self.year_patterns = year_patterns or self.YEAR_PATTERNS
        self.ignore_patterns = ignore_patterns or self.IGNORE_PATTERNS

    def discover(self) -> List[DiscoveredDocument]:
        """
        Discover all documents in the base path.

        Returns:
            List of DiscoveredDocument objects
        """
        if not self.base_path.exists():
            logger.warning(f"Base path does not exist: {self.base_path}")
            return []

        documents = []

        for ext in self.supported_extensions:
            pattern = str(self.base_path / "**" / f"*{ext}")
            for file_path in glob.glob(pattern, recursive=True):
                # Check ignore patterns
                if any(p in file_path for p in self.ignore_patterns):
                    continue

                try:
                    doc = self._load_document(file_path)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")

        logger.info(f"Discovered {len(documents)} documents")
        return documents

    def discover_from_dict(self, documents_dict: Dict[str, str]) -> List[DiscoveredDocument]:
        """
        Create documents from a dictionary (for testing/direct input).

        Args:
            documents_dict: Dict mapping doc_id to content

        Returns:
            List of DiscoveredDocument objects
        """
        documents = []
        for doc_id, content in documents_dict.items():
            year, category = self._extract_metadata_from_id(doc_id)
            doc = DiscoveredDocument(
                doc_id=doc_id,
                content=content,
                file_path="",
                file_name=doc_id,
                year=year,
                category=category,
                word_count=len(content.split()),
            )
            documents.append(doc)
        return documents

    def _load_document(self, file_path: str) -> Optional[DiscoveredDocument]:
        """Load a single document from file."""
        path = Path(file_path)

        if not path.exists():
            return None

        # Read content based on extension
        ext = path.suffix.lower()
        if ext in {".txt", ".md"}:
            content = self._read_text_file(path)
        elif ext == ".json":
            content = self._read_json_file(path)
        elif ext == ".pdf":
            content = self._read_pdf_file(path)
        else:
            return None

        if not content or not content.strip():
            logger.warning(f"Empty content in {file_path}")
            return None

        # Generate doc_id from path
        doc_id = self._generate_doc_id(path)

        # Extract metadata
        year = self._extract_year(path)
        category = self._extract_category(path)

        return DiscoveredDocument(
            doc_id=doc_id,
            content=content,
            file_path=str(path.absolute()),
            file_name=path.name,
            year=year,
            category=category,
            file_size=path.stat().st_size,
            file_extension=ext,
            word_count=len(content.split()),
        )

    def _read_text_file(self, path: Path) -> str:
        """Read text file with encoding detection."""
        encodings = ["utf-8", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        logger.warning(f"Could not decode {path}")
        return ""

    def _read_json_file(self, path: Path) -> str:
        """Read JSON file and extract text content."""
        import json
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Handle common JSON structures
            if isinstance(data, str):
                return data
            elif isinstance(data, dict):
                # Try common text fields
                for field in ["text", "content", "body", "abstract"]:
                    if field in data:
                        return str(data[field])
                # Fallback to string representation
                return json.dumps(data)
            elif isinstance(data, list):
                return "\n".join(str(item) for item in data)
            return str(data)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {path}: {e}")
            return ""

    def _read_pdf_file(self, path: Path) -> str:
        """Read PDF file (requires PyMuPDF or similar)."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            logger.warning("PyMuPDF not installed, skipping PDF")
            return ""
        except Exception as e:
            logger.warning(f"Error reading PDF {path}: {e}")
            return ""

    def _generate_doc_id(self, path: Path) -> str:
        """Generate unique document ID from path."""
        # Use relative path from base, remove extension
        try:
            relative = path.relative_to(self.base_path)
            doc_id = str(relative.with_suffix("")).replace(os.sep, "_")
        except ValueError:
            doc_id = path.stem
        return doc_id

    def _extract_year(self, path: Path) -> int:
        """Extract publication year from path."""
        # Try custom extractor first
        if self.year_extractor:
            year = self.year_extractor(str(path))
            if year:
                return year

        # Try patterns on filename
        filename = path.stem
        for pattern in self.year_patterns:
            match = re.search(pattern, filename)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2100:
                    return year

        # Try parent folder names
        for parent in path.parents:
            if parent == self.base_path:
                break
            for pattern in self.year_patterns:
                match = re.search(pattern, parent.name)
                if match:
                    year = int(match.group(1))
                    if 1900 <= year <= 2100:
                        return year

        return self.default_year

    def _extract_category(self, path: Path) -> str:
        """Extract category from path."""
        # Try custom extractor first
        if self.category_extractor:
            category = self.category_extractor(str(path))
            if category:
                return category

        # Extract from parent folder
        if self.category_from_folder:
            try:
                relative = path.relative_to(self.base_path)
                parts = relative.parts
                if len(parts) > 1:
                    # Use first subdirectory as category
                    return parts[0].lower().replace(" ", "_")
            except ValueError:
                pass

        return self.default_category

    def _extract_metadata_from_id(self, doc_id: str) -> tuple:
        """Extract year and category from document ID string."""
        year = self.default_year
        category = self.default_category

        # Try to find year in doc_id
        for pattern in self.year_patterns:
            match = re.search(pattern, doc_id)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2100:
                    break

        # Try to extract category (first part before underscore or hyphen)
        parts = re.split(r"[_-]", doc_id)
        if parts:
            # Skip if first part is a year
            if not parts[0].isdigit():
                category = parts[0].lower()

        return year, category

    def get_statistics(self, documents: List[DiscoveredDocument]) -> Dict[str, Any]:
        """Get statistics about discovered documents."""
        if not documents:
            return {"total": 0}

        years = [d.year for d in documents]
        categories = [d.category for d in documents]
        word_counts = [d.word_count for d in documents]

        return {
            "total": len(documents),
            "total_words": sum(word_counts),
            "avg_words": sum(word_counts) / len(word_counts),
            "min_words": min(word_counts),
            "max_words": max(word_counts),
            "years": sorted(set(years)),
            "categories": sorted(set(categories)),
            "by_year": {y: years.count(y) for y in set(years)},
            "by_category": {c: categories.count(c) for c in set(categories)},
        }
