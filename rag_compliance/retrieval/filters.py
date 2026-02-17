"""
Metadata Filters for retrieval-time filtering.

Provides filter definitions and matching logic to narrow down
retrieved results by act, section, rule, form, topic, entity_type, etc.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger("rag_compliance.retrieval.filters")


@dataclass
class MetadataFilter:
    """Filter criteria for narrowing retrieval results.

    All fields are optional. Only non-None fields are applied.
    String matching is case-insensitive and uses substring containment.
    """

    act: Optional[str] = None
    section: Optional[str] = None
    rule: Optional[str] = None
    form: Optional[str] = None
    topic: Optional[str] = None
    entity_type: Optional[str] = None  # "Company" or "LLP"
    source_type: Optional[str] = None  # "act", "rule", "form", "circular"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with only non-None values for FAISS search."""
        return {k: v for k, v in {
            "act": self.act,
            "section": self.section,
            "rule": self.rule,
            "form": self.form,
            "topic": self.topic,
            "entity_type": self.entity_type,
            "source_type": self.source_type,
        }.items() if v is not None}

    @property
    def is_empty(self) -> bool:
        """Return True if no filters are set."""
        return all(
            v is None for v in [
                self.act, self.section, self.rule, self.form,
                self.topic, self.entity_type, self.source_type,
            ]
        )


def apply_filters(
    results: list[Any],
    metadata_filter: MetadataFilter,
) -> list[Any]:
    """Apply metadata filters to a list of search results.

    Args:
        results: List of SearchResult objects with .metadata attribute.
        metadata_filter: Filter criteria to apply.

    Returns:
        Filtered list of results matching all specified criteria.
    """
    if metadata_filter.is_empty:
        return results

    filter_dict = metadata_filter.to_dict()
    filtered = []

    for result in results:
        metadata = result.metadata if hasattr(result, "metadata") else {}
        if _matches(metadata, filter_dict):
            filtered.append(result)

    logger.info(
        "Filter applied: %d → %d results (filters: %s)",
        len(results),
        len(filtered),
        filter_dict,
    )

    return filtered


def _matches(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Check if metadata matches all filter criteria.

    Args:
        metadata: Document metadata dict.
        filters: Filter criteria dict (non-None values only).

    Returns:
        True if all filters match.
    """
    for key, value in filters.items():
        meta_value = metadata.get(key)
        if meta_value is None:
            return False
        if isinstance(value, str) and isinstance(meta_value, str):
            if value.lower() not in meta_value.lower():
                return False
        elif meta_value != value:
            return False
    return True
