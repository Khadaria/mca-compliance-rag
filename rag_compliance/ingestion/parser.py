"""
PDF Document Parser for MCA Compliance corpus.

Extracts text from PDF files page-by-page using PyMuPDF (fitz).
Handles encoding issues, empty pages, and provides structured output
for downstream chunking and metadata extraction.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger("rag_compliance.ingestion.parser")


@dataclass
class PageContent:
    """Represents extracted text from a single PDF page."""

    page_number: int
    text: str


@dataclass
class ParsedDocument:
    """Represents a fully parsed PDF document."""

    filename: str
    filepath: str
    total_pages: int
    pages: list[PageContent] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Return concatenated text from all pages."""
        return "\n\n".join(page.text for page in self.pages if page.text.strip())


class PDFParser:
    """Parses PDF documents and extracts structured text content.

    Uses PyMuPDF for fast, reliable text extraction. Handles:
    - Multi-page documents
    - Empty or image-only pages (logged as warnings)
    - Unicode normalization
    """

    def __init__(self) -> None:
        """Initialize the PDF parser."""
        logger.info("PDFParser initialized")

    def parse(self, filepath: str | Path) -> ParsedDocument:
        """Parse a single PDF file and extract text from all pages.

        Args:
            filepath: Path to the PDF file to parse.

        Returns:
            ParsedDocument containing extracted text organized by page.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            RuntimeError: If the PDF cannot be opened or parsed.
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"PDF file not found: {filepath}")

        if not filepath.suffix.lower() == ".pdf":
            raise ValueError(f"Expected a PDF file, got: {filepath.suffix}")

        logger.info("Parsing PDF: %s", filepath.name)

        try:
            doc = fitz.open(str(filepath))
        except Exception as e:
            raise RuntimeError(f"Failed to open PDF '{filepath.name}': {e}") from e

        pages: list[PageContent] = []
        empty_page_count = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            # Clean up extracted text
            text = self._clean_text(text)

            if not text.strip():
                empty_page_count += 1
                logger.debug(
                    "Empty page %d in '%s' (possibly scanned/image)",
                    page_num + 1,
                    filepath.name,
                )
                continue

            pages.append(PageContent(page_number=page_num + 1, text=text))

        total_pages = len(doc)
        doc.close()

        if empty_page_count > 0:
            logger.warning(
                "%d empty pages in '%s' (total: %d pages)",
                empty_page_count,
                filepath.name,
                total_pages,
            )

        if not pages:
            logger.warning(
                "No text extracted from '%s' — file may be scanned/image-based",
                filepath.name,
            )

        parsed = ParsedDocument(
            filename=filepath.name,
            filepath=str(filepath),
            total_pages=total_pages,
            pages=pages,
        )

        logger.info(
            "Parsed '%s': %d pages with text out of %d total",
            filepath.name,
            len(pages),
            parsed.total_pages,
        )

        return parsed

    def parse_directory(self, directory: str | Path) -> list[ParsedDocument]:
        """Parse all PDF files in a directory.

        Args:
            directory: Path to directory containing PDF files.

        Returns:
            List of ParsedDocument instances for each successfully parsed PDF.
        """
        directory = Path(directory)

        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        pdf_files = sorted(directory.glob("*.pdf"))
        logger.info("Found %d PDF files in '%s'", len(pdf_files), directory)

        documents: list[ParsedDocument] = []
        for pdf_path in pdf_files:
            try:
                doc = self.parse(pdf_path)
                documents.append(doc)
            except Exception as e:
                logger.error("Failed to parse '%s': %s", pdf_path.name, e)
                continue

        logger.info(
            "Successfully parsed %d / %d PDFs", len(documents), len(pdf_files)
        )
        return documents

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text by normalizing whitespace and encoding.

        Args:
            text: Raw text extracted from PDF page.

        Returns:
            Cleaned text string.
        """
        # Normalize unicode characters
        import unicodedata

        text = unicodedata.normalize("NFKD", text)

        # Replace multiple consecutive newlines with double newline
        import re

        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace multiple spaces with single space (preserve newlines)
        text = re.sub(r"[^\S\n]+", " ", text)

        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()
