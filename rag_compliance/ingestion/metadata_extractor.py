"""
Metadata Extractor for MCA Compliance corpus chunks.

Infers structured metadata from chunk content and source filename:
- act, section, rule, form
- topic, entity_type, source_type
- effective_from, effective_to (when detectable)

This metadata powers filtering during retrieval.
"""

import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from rag_compliance.ingestion.chunker import DocumentChunk

logger = logging.getLogger("rag_compliance.ingestion.metadata_extractor")


# ── Filename → metadata mapping ──────────────────────────────────────
FILENAME_RULES: list[dict] = [
    {
        "pattern": re.compile(r"Companies Act", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "act",
    },
    {
        "pattern": re.compile(r"LLP.?Act", re.IGNORECASE),
        "act": "LLP Act, 2008",
        "entity_type": "LLP",
        "source_type": "act",
    },
    {
        "pattern": re.compile(r"LLP.*Rules", re.IGNORECASE),
        "act": "LLP Act, 2008",
        "entity_type": "LLP",
        "source_type": "rule",
    },
    {
        "pattern": re.compile(r"Companies.*\(Accounts\).*Rules", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "rule",
        "topic": "Accounts",
    },
    {
        "pattern": re.compile(r"Companies.*\(Appointment.*Directors?\).*Rules", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "rule",
        "topic": "Directors",
    },
    {
        "pattern": re.compile(r"Companies.*\(Incorporation\).*Rules", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "rule",
        "topic": "Incorporation",
    },
    {
        "pattern": re.compile(r"Companies.*\(Management.*Administration\).*Rules", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "rule",
        "topic": "Management and Administration",
    },
    {
        "pattern": re.compile(r"Form.*MGT", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "form",
        "topic": "Management and Administration",
    },
    {
        "pattern": re.compile(r"Form.*DIR", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "form",
        "topic": "Directors",
    },
    {
        "pattern": re.compile(r"Form.*INC", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "form",
        "topic": "Incorporation",
    },
    {
        "pattern": re.compile(r"Form.*AOC", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "form",
        "topic": "Accounts",
    },
    {
        "pattern": re.compile(r"Form.*8.*LLP|LLP.*Form.*8", re.IGNORECASE),
        "act": "LLP Act, 2008",
        "entity_type": "LLP",
        "source_type": "form",
        "topic": "Annual Filing",
    },
    {
        "pattern": re.compile(r"Form.*11.*LLP|LLP.*Form.*11", re.IGNORECASE),
        "act": "LLP Act, 2008",
        "entity_type": "LLP",
        "source_type": "form",
        "topic": "Annual Return",
    },
    {
        "pattern": re.compile(r"Ch9.*Annexure|Annexure.*Rules", re.IGNORECASE),
        "act": "Companies Act, 2013",
        "entity_type": "Company",
        "source_type": "rule",
    },
]

# ── Topic detection from content ──────────────────────────────────────
TOPIC_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Annual Return", re.compile(r"annual return|MGT-7|MGT-7A", re.IGNORECASE)),
    ("Annual Filing", re.compile(r"annual filing|financial statement|balance sheet|AOC-4", re.IGNORECASE)),
    ("Directors", re.compile(r"director|DIN|DIR-3|KYC|appointment of director", re.IGNORECASE)),
    ("Incorporation", re.compile(r"incorporat|INC-\d+|certificate of incorporation|registered office", re.IGNORECASE)),
    ("Accounts", re.compile(r"accounts|audit|auditor|financial year|books of account", re.IGNORECASE)),
    ("Penalties", re.compile(r"penalty|penalti|fine|compounding|additional fee", re.IGNORECASE)),
    ("LLP Agreement", re.compile(r"llp agreement|partnership deed|designated partner", re.IGNORECASE)),
    ("Compliance", re.compile(r"complianc|filing|due date|deadline|time limit", re.IGNORECASE)),
    ("Meetings", re.compile(r"meeting|AGM|annual general meeting|board meeting|resolution", re.IGNORECASE)),
    ("Share Capital", re.compile(r"share capital|shares|allotment|transfer of shares", re.IGNORECASE)),
    ("Charges", re.compile(r"charge|CHG-|modification of charge|satisfaction", re.IGNORECASE)),
    ("Winding Up", re.compile(r"winding up|dissolution|liquidat|striking off", re.IGNORECASE)),
]


@dataclass
class ChunkMetadata:
    """Structured metadata for a document chunk, used for filtering during retrieval."""

    act: Optional[str] = None
    section: Optional[str] = None
    rule: Optional[str] = None
    form: Optional[str] = None
    chapter: Optional[str] = None
    topic: Optional[str] = None
    entity_type: Optional[str] = None  # "Company" or "LLP"
    source_type: Optional[str] = None  # "act", "rule", "form", "circular"
    source_file: str = ""
    page_numbers: list[int] = field(default_factory=list)
    chunk_id: str = ""
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert metadata to a flat dictionary for storage."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != "" and v != []}


class MetadataExtractor:
    """Extracts and enriches metadata for document chunks.

    Combines:
    1. Filename-based inference (act, entity_type, source_type)
    2. Chunk-level structural metadata (section, rule, form from chunker)
    3. Content-based topic detection (regex patterns on chunk text)
    """

    def __init__(self) -> None:
        logger.info("MetadataExtractor initialized")

    def extract(self, chunk: DocumentChunk) -> ChunkMetadata:
        """Extract metadata for a single document chunk.

        Args:
            chunk: A DocumentChunk from the chunker module.

        Returns:
            ChunkMetadata with all inferable fields populated.
        """
        metadata = ChunkMetadata(
            chunk_id=chunk.chunk_id,
            source_file=chunk.source_file,
            page_numbers=chunk.page_numbers,
            section=chunk.section,
            rule=chunk.rule,
            form=chunk.form,
            chapter=chunk.chapter,
        )

        # Enrich from filename
        self._enrich_from_filename(metadata, chunk.source_file)

        # Detect topic from content
        if not metadata.topic:
            metadata.topic = self._detect_topic(chunk.text)

        # Detect form references in content
        if not metadata.form:
            metadata.form = self._detect_form(chunk.text)

        # Detect section references in content
        if not metadata.section:
            metadata.section = self._detect_section(chunk.text)

        # Detect effective dates
        self._detect_dates(metadata, chunk.text)

        return metadata

    def extract_batch(self, chunks: list[DocumentChunk]) -> list[ChunkMetadata]:
        """Extract metadata for a batch of chunks.

        Args:
            chunks: List of DocumentChunk instances.

        Returns:
            List of ChunkMetadata instances, one per chunk.
        """
        metadatas = [self.extract(chunk) for chunk in chunks]

        logger.info(
            "Extracted metadata for %d chunks — topics: %s",
            len(metadatas),
            set(m.topic for m in metadatas if m.topic),
        )

        return metadatas

    def _enrich_from_filename(self, metadata: ChunkMetadata, filename: str) -> None:
        """Infer metadata fields from the source filename.

        Args:
            metadata: ChunkMetadata to enrich in-place.
            filename: Source filename to match against patterns.
        """
        for rule in FILENAME_RULES:
            if rule["pattern"].search(filename):
                if not metadata.act:
                    metadata.act = rule.get("act")
                if not metadata.entity_type:
                    metadata.entity_type = rule.get("entity_type")
                if not metadata.source_type:
                    metadata.source_type = rule.get("source_type")
                if not metadata.topic and "topic" in rule:
                    metadata.topic = rule.get("topic")
                break  # Use first match

    @staticmethod
    def _detect_topic(text: str) -> Optional[str]:
        """Detect the most relevant topic from chunk text.

        Args:
            text: Chunk text content.

        Returns:
            Topic string if detected, None otherwise.
        """
        # Check first 500 chars for topic signals
        sample = text[:500]
        for topic_name, pattern in TOPIC_PATTERNS:
            if pattern.search(sample):
                return topic_name
        return None

    @staticmethod
    def _detect_form(text: str) -> Optional[str]:
        """Detect form references in chunk text.

        Args:
            text: Chunk text content.

        Returns:
            Form identifier if found, None otherwise.
        """
        form_pattern = re.compile(
            r"(?:Form\s+(?:No\.?\s*)?)?(MGT-7A?|AOC-4|DIR-3\s*KYC|INC-\d+[A-Z]?|CHG-\d+|LLP\s*Form\s*\d+)",
            re.IGNORECASE,
        )
        match = form_pattern.search(text[:500])
        return match.group(1).strip().upper() if match else None

    @staticmethod
    def _detect_section(text: str) -> Optional[str]:
        """Detect section number references in chunk text.

        Args:
            text: Chunk text content.

        Returns:
            Section number if found, None otherwise.
        """
        section_pattern = re.compile(
            r"(?:Section|Sec\.?)\s+(\d+[A-Z]?)", re.IGNORECASE
        )
        match = section_pattern.search(text[:300])
        return match.group(1) if match else None

    @staticmethod
    def _detect_dates(metadata: ChunkMetadata, text: str) -> None:
        """Detect effective dates in chunk text.

        Args:
            metadata: ChunkMetadata to enrich in-place.
            text: Chunk text content.
        """
        # Common date patterns in Indian legal documents
        date_pattern = re.compile(
            r"(?:w\.?e\.?f\.?|with effect from|effective from|notified on)\s+"
            r"(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+\w+,?\s+\d{4})",
            re.IGNORECASE,
        )
        match = date_pattern.search(text)
        if match:
            metadata.effective_from = match.group(1).strip()
