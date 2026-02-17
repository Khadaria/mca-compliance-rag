"""
Document Chunker for MCA Compliance corpus.

Splits parsed documents into semantically meaningful chunks using:
1. Regex-based section/rule/form boundary detection (preferred)
2. Fixed-size fallback chunking with overlap (for unstructured content)

Each chunk carries source metadata for downstream embedding and retrieval.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from rag_compliance.config import get_settings
from rag_compliance.ingestion.parser import ParsedDocument

logger = logging.getLogger("rag_compliance.ingestion.chunker")

# ── Section/Rule/Form boundary patterns ────────────────────────────────
SECTION_PATTERNS = [
    # "Section 92" or "Section 92." or "SECTION 92"
    re.compile(r"^(?:SECTION|Section)\s+(\d+[A-Z]?)\b\.?", re.MULTILINE),
    # "92. (1) Every company shall..."
    re.compile(r"^(\d{1,4})\.\s*\(1\)\s+", re.MULTILINE),
]

RULE_PATTERNS = [
    # "Rule 11" or "RULE 11"
    re.compile(r"^(?:RULE|Rule)\s+(\d+[A-Z]?)\b\.?", re.MULTILINE),
]

FORM_PATTERNS = [
    # "Form MGT-7" or "FORM AOC-4" or "Form No. DIR-3 KYC"
    re.compile(
        r"^(?:FORM|Form)\s+(?:No\.?\s*)?([A-Z]+-?\d*[A-Z]*(?:\s+KYC)?)",
        re.MULTILINE,
    ),
]

CHAPTER_PATTERNS = [
    # "CHAPTER IX" or "Chapter IX"
    re.compile(r"^(?:CHAPTER|Chapter)\s+([IVXLCDM]+|\d+)", re.MULTILINE),
]

# Combined pattern for splitting — matches any structural boundary
BOUNDARY_PATTERN = re.compile(
    r"(?=^(?:SECTION|Section)\s+\d+[A-Z]?\b)"
    r"|(?=^(?:RULE|Rule)\s+\d+[A-Z]?\b)"
    r"|(?=^(?:CHAPTER|Chapter)\s+(?:[IVXLCDM]+|\d+))"
    r"|(?=^\d{1,4}\.\s*\(1\)\s+)",
    re.MULTILINE,
)


@dataclass
class DocumentChunk:
    """A single chunk of text with provenance metadata."""

    chunk_id: str
    text: str
    source_file: str
    page_numbers: list[int] = field(default_factory=list)
    section: Optional[str] = None
    rule: Optional[str] = None
    form: Optional[str] = None
    chapter: Optional[str] = None
    chunk_index: int = 0

    @property
    def char_count(self) -> int:
        """Return the character count of the chunk text."""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """Return the approximate word count."""
        return len(self.text.split())


class DocumentChunker:
    """Splits parsed documents into retrieval-friendly chunks.

    Uses a two-pass strategy:
    1. Attempt regex-based splitting on section/rule/chapter boundaries
    2. Fall back to fixed-size overlapping chunks for unstructured content

    Args:
        chunk_size: Maximum characters per chunk (for fallback splitting).
        chunk_overlap: Overlap characters between consecutive chunks.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        logger.info(
            "DocumentChunker initialized (chunk_size=%d, overlap=%d)",
            self.chunk_size,
            self.chunk_overlap,
        )

    def chunk(self, document: ParsedDocument) -> list[DocumentChunk]:
        """Chunk a parsed document into retrieval-ready pieces.

        Args:
            document: A ParsedDocument from the parser module.

        Returns:
            List of DocumentChunk instances with text and metadata.
        """
        full_text = document.full_text

        if not full_text.strip():
            logger.warning("Empty document: '%s'", document.filename)
            return []

        # Try structural splitting first
        structural_chunks = self._split_by_structure(full_text)

        if len(structural_chunks) > 1:
            logger.info(
                "Structural splitting for '%s': %d chunks",
                document.filename,
                len(structural_chunks),
            )
            chunks = self._process_structural_chunks(
                structural_chunks, document
            )
        else:
            logger.info(
                "Fallback to fixed-size chunking for '%s'", document.filename
            )
            chunks = self._split_fixed_size(full_text, document)

        # Post-process: split any oversized chunks
        final_chunks = []
        for chunk in chunks:
            if chunk.char_count > self.chunk_size * 2:
                sub_chunks = self._split_oversized_chunk(chunk)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        # Assign sequential IDs
        for idx, chunk in enumerate(final_chunks):
            chunk.chunk_index = idx
            chunk.chunk_id = f"{document.filename}::chunk_{idx:04d}"

        logger.info(
            "Chunked '%s': %d final chunks (avg %d chars)",
            document.filename,
            len(final_chunks),
            sum(c.char_count for c in final_chunks) // max(len(final_chunks), 1),
        )

        return final_chunks

    def _split_by_structure(self, text: str) -> list[str]:
        """Split text on section/rule/chapter boundaries.

        Args:
            text: Full document text.

        Returns:
            List of text segments split at structural boundaries.
        """
        parts = BOUNDARY_PATTERN.split(text)
        # Filter out empty segments
        return [p.strip() for p in parts if p.strip()]

    def _process_structural_chunks(
        self, segments: list[str], document: ParsedDocument
    ) -> list[DocumentChunk]:
        """Convert raw text segments into DocumentChunk instances with metadata.

        Args:
            segments: Text segments from structural splitting.
            document: Source ParsedDocument for provenance.

        Returns:
            List of DocumentChunk instances.
        """
        chunks: list[DocumentChunk] = []

        for idx, segment in enumerate(segments):
            section = self._extract_pattern(segment, SECTION_PATTERNS)
            rule = self._extract_pattern(segment, RULE_PATTERNS)
            form = self._extract_pattern(segment, FORM_PATTERNS)
            chapter = self._extract_pattern(segment, CHAPTER_PATTERNS)

            # Determine which pages this chunk came from
            page_numbers = self._find_page_numbers(segment, document)

            chunk = DocumentChunk(
                chunk_id="",  # Assigned later
                text=segment,
                source_file=document.filename,
                page_numbers=page_numbers,
                section=section,
                rule=rule,
                form=form,
                chapter=chapter,
            )
            chunks.append(chunk)

        return chunks

    def _split_fixed_size(
        self, text: str, document: ParsedDocument
    ) -> list[DocumentChunk]:
        """Split text into fixed-size chunks with overlap.

        Args:
            text: Full document text.
            document: Source document for provenance.

        Returns:
            List of DocumentChunk instances.
        """
        chunks: list[DocumentChunk] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at a paragraph or sentence boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = text.rfind(". ", start, end)
                    if sent_break > start + self.chunk_size // 2:
                        end = sent_break + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                page_numbers = self._find_page_numbers(chunk_text, document)
                chunk = DocumentChunk(
                    chunk_id="",
                    text=chunk_text,
                    source_file=document.filename,
                    page_numbers=page_numbers,
                )
                chunks.append(chunk)

            # Move start forward, accounting for overlap
            start = max(start + 1, end - self.chunk_overlap)

        return chunks

    def _split_oversized_chunk(self, chunk: DocumentChunk) -> list[DocumentChunk]:
        """Split an oversized chunk into smaller pieces.

        Args:
            chunk: A DocumentChunk that exceeds the size limit.

        Returns:
            List of smaller DocumentChunk instances.
        """
        text = chunk.text
        sub_chunks: list[DocumentChunk] = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            if end < len(text):
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break

            sub_text = text[start:end].strip()
            if sub_text:
                sub_chunk = DocumentChunk(
                    chunk_id="",
                    text=sub_text,
                    source_file=chunk.source_file,
                    page_numbers=chunk.page_numbers,
                    section=chunk.section,
                    rule=chunk.rule,
                    form=chunk.form,
                    chapter=chunk.chapter,
                )
                sub_chunks.append(sub_chunk)

            start = max(start + 1, end - self.chunk_overlap)

        return sub_chunks

    @staticmethod
    def _extract_pattern(
        text: str, patterns: list[re.Pattern]
    ) -> Optional[str]:
        """Extract the first matching group from a list of regex patterns.

        Args:
            text: Text to search.
            patterns: List of compiled regex patterns.

        Returns:
            First captured group from the first matching pattern, or None.
        """
        # Only check the first few lines for headers
        header = text[:300]
        for pattern in patterns:
            match = pattern.search(header)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _find_page_numbers(
        chunk_text: str, document: ParsedDocument
    ) -> list[int]:
        """Determine which source pages a chunk's text came from.

        Uses a simple substring match against page texts.

        Args:
            chunk_text: The chunk text to locate.
            document: The source ParsedDocument.

        Returns:
            List of page numbers where the chunk text appears.
        """
        # Use a short prefix for matching to avoid performance issues
        search_text = chunk_text[:100]
        pages = []
        for page in document.pages:
            if search_text in page.text:
                pages.append(page.page_number)
        return pages if pages else [1]  # Default to page 1 if no match
