"""
FAISS-based Vector Store for MCA Compliance RAG system.

Stores document embeddings with associated metadata in a FAISS index.
Uses IndexFlatIP (inner product on L2-normalized vectors = cosine similarity).
Metadata is stored in a parallel JSON sidecar file.

Supports:
- Adding chunks with embeddings and metadata
- Similarity search with optional metadata filtering
- Persistence (save/load to disk)
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import faiss
import numpy as np

from rag_compliance.config import get_settings
from rag_compliance.embeddings.embedder import Embedder

logger = logging.getLogger("rag_compliance.embeddings.vector_store")


@dataclass
class SearchResult:
    """A single search result from the vector store."""

    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any]
    rank: int


class VectorStore:
    """FAISS-backed vector store with metadata sidecar.

    Stores embeddings in a FAISS IndexFlatIP index and metadata
    in a parallel list, persisted as JSON. Supports add, search,
    save, and load operations.

    Args:
        embedder: Embedder instance for generating query embeddings.
        store_dir: Directory for persisting the index and metadata.
    """

    INDEX_FILENAME = "faiss_index.bin"
    METADATA_FILENAME = "metadata.json"
    TEXTS_FILENAME = "texts.json"

    def __init__(
        self,
        embedder: Embedder,
        store_dir: str | None = None,
    ) -> None:
        settings = get_settings()
        self.embedder = embedder
        self.dimension = settings.embedding_dimension
        self.store_dir = Path(store_dir or settings.vector_store_dir)

        # Initialize FAISS index — inner product on normalized vectors = cosine sim
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.dimension)

        # Parallel storage for metadata and texts
        self._metadata: list[dict[str, Any]] = []
        self._texts: list[str] = []

        logger.info(
            "VectorStore initialized (dimension=%d, store_dir=%s)",
            self.dimension,
            self.store_dir,
        )

    @property
    def size(self) -> int:
        """Return the number of vectors in the index."""
        return self.index.ntotal

    def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]],
        batch_size: int = 64,
    ) -> int:
        """Add texts with metadata to the vector store.

        Generates embeddings and adds them to the FAISS index.

        Args:
            texts: List of text strings to embed and store.
            metadatas: List of metadata dicts, one per text. Must match length of texts.
            batch_size: Batch size for embedding generation.

        Returns:
            Number of texts successfully added.

        Raises:
            ValueError: If texts and metadatas have different lengths.
        """
        if len(texts) != len(metadatas):
            raise ValueError(
                f"Mismatch: {len(texts)} texts vs {len(metadatas)} metadatas"
            )

        if not texts:
            logger.warning("No texts to add")
            return 0

        logger.info("Adding %d texts to vector store...", len(texts))

        # Generate embeddings
        embeddings = self.embedder.embed_batch(texts, batch_size=batch_size)

        # Add to FAISS index
        self.index.add(embeddings)

        # Store metadata and texts
        self._metadata.extend(metadatas)
        self._texts.extend(texts)

        logger.info(
            "Added %d vectors. Total index size: %d",
            len(texts),
            self.size,
        )

        return len(texts)

    def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """Search the vector store for similar documents.

        Args:
            query: Query text to search for.
            top_k: Number of results to return. Defaults to config value.
            filters: Optional metadata filters to apply post-retrieval.

        Returns:
            List of SearchResult instances, sorted by descending score.
        """
        settings = get_settings()
        top_k = top_k or settings.top_k

        if self.size == 0:
            logger.warning("Vector store is empty — no results")
            return []

        # Embed the query
        query_embedding = self.embedder.embed_text(query)
        query_embedding = query_embedding.reshape(1, -1)

        # Search with expanded k if filters are applied (to allow post-filtering)
        search_k = min(top_k * 3 if filters else top_k, self.size)

        scores, indices = self.index.search(query_embedding, search_k)

        results: list[SearchResult] = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for padding
                continue

            idx = int(idx)
            metadata = self._metadata[idx] if idx < len(self._metadata) else {}
            text = self._texts[idx] if idx < len(self._texts) else ""

            # Apply metadata filters
            if filters and not self._matches_filters(metadata, filters):
                continue

            results.append(
                SearchResult(
                    chunk_id=metadata.get("chunk_id", f"idx_{idx}"),
                    text=text,
                    score=float(score),
                    metadata=metadata,
                    rank=rank,
                )
            )

            if len(results) >= top_k:
                break

        logger.info(
            "Search for '%s...' returned %d results (top score: %.4f)",
            query[:50],
            len(results),
            results[0].score if results else 0.0,
        )

        return results

    @staticmethod
    def _matches_filters(
        metadata: dict[str, Any], filters: dict[str, Any]
    ) -> bool:
        """Check if metadata matches all specified filters.

        Args:
            metadata: Document metadata to check.
            filters: Filter criteria to match against.

        Returns:
            True if all filters match, False otherwise.
        """
        for key, value in filters.items():
            if value is None:
                continue
            meta_value = metadata.get(key)
            if meta_value is None:
                return False
            # Case-insensitive string matching
            if isinstance(value, str) and isinstance(meta_value, str):
                if value.lower() not in meta_value.lower():
                    return False
            elif meta_value != value:
                return False
        return True

    def save(self) -> None:
        """Persist the index and metadata to disk.

        Creates the store directory if it doesn't exist.
        """
        self.store_dir.mkdir(parents=True, exist_ok=True)

        index_path = self.store_dir / self.INDEX_FILENAME
        metadata_path = self.store_dir / self.METADATA_FILENAME
        texts_path = self.store_dir / self.TEXTS_FILENAME

        # Save FAISS index
        faiss.write_index(self.index, str(index_path))

        # Save metadata
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)

        # Save texts
        with open(texts_path, "w", encoding="utf-8") as f:
            json.dump(self._texts, f, ensure_ascii=False, indent=2)

        logger.info(
            "Vector store saved to '%s' (%d vectors)", self.store_dir, self.size
        )

    def load(self) -> bool:
        """Load the index and metadata from disk.

        Returns:
            True if successfully loaded, False if files not found.
        """
        index_path = self.store_dir / self.INDEX_FILENAME
        metadata_path = self.store_dir / self.METADATA_FILENAME
        texts_path = self.store_dir / self.TEXTS_FILENAME

        if not index_path.exists():
            logger.info("No existing index found at '%s'", index_path)
            return False

        # Load FAISS index
        self.index = faiss.read_index(str(index_path))

        # Load metadata
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

        # Load texts
        if texts_path.exists():
            with open(texts_path, "r", encoding="utf-8") as f:
                self._texts = json.load(f)

        logger.info(
            "Vector store loaded from '%s' (%d vectors)",
            self.store_dir,
            self.size,
        )

        return True

    def clear(self) -> None:
        """Clear the index and all associated data."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self._metadata.clear()
        self._texts.clear()
        logger.info("Vector store cleared")
