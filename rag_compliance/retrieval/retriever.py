"""
Retriever for MCA Compliance RAG system.

Orchestrates the retrieval pipeline:
1. Embed the query
2. Search the FAISS vector store
3. Apply metadata filters
4. Rerank results
5. Return structured results
"""

import logging
from typing import Any, Optional

from rag_compliance.config import get_settings
from rag_compliance.embeddings.embedder import Embedder
from rag_compliance.embeddings.vector_store import SearchResult, VectorStore
from rag_compliance.retrieval.filters import MetadataFilter, apply_filters
from rag_compliance.retrieval.reranker import Reranker

logger = logging.getLogger("rag_compliance.retrieval.retriever")


class Retriever:
    """Orchestrates query → embedding → search → filter → rerank pipeline.

    Args:
        vector_store: Initialized VectorStore with loaded index.
        embedder: Embedder instance (shared with vector store).
        reranker: Optional Reranker instance.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        reranker: Optional[Reranker] = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedder = embedder
        self.reranker = reranker or Reranker()

        logger.info(
            "Retriever initialized (index size: %d)", vector_store.size
        )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: Optional[MetadataFilter] = None,
    ) -> list[SearchResult]:
        """Retrieve the most relevant document chunks for a query.

        Args:
            query: Natural language query from the user.
            top_k: Number of results to return. Defaults to config.
            filters: Optional metadata filters to narrow results.

        Returns:
            List of SearchResult instances sorted by relevance.
        """
        settings = get_settings()
        top_k = top_k or settings.top_k

        logger.info("Retrieving for query: '%s...' (top_k=%d)", query[:80], top_k)

        # Step 1: Search the vector store (with filters if provided)
        filter_dict = filters.to_dict() if filters and not filters.is_empty else None
        results = self.vector_store.search(
            query=query,
            top_k=top_k * 2,  # Over-fetch for reranking headroom
            filters=filter_dict,
        )

        # Step 2: Apply additional filters if needed
        if filters and not filters.is_empty:
            results = apply_filters(results, filters)

        # Step 3: Rerank
        results = self.reranker.rerank(query, results, top_k=top_k)

        # Step 4: Score threshold filtering
        threshold = settings.retrieval_score_threshold
        results = [r for r in results if r.score >= threshold]

        logger.info(
            "Retrieved %d results (threshold=%.2f)", len(results), threshold
        )

        for i, r in enumerate(results[:3]):
            logger.debug(
                "  [%d] score=%.4f, section=%s, source=%s, text='%s...'",
                i,
                r.score,
                r.metadata.get("section", "N/A"),
                r.metadata.get("source_file", "N/A"),
                r.text[:80],
            )

        return results

    def retrieve_with_context(
        self,
        query: str,
        top_k: int | None = None,
        filters: Optional[MetadataFilter] = None,
    ) -> dict[str, Any]:
        """Retrieve results and format as a context dict for the generator.

        Args:
            query: Natural language query from the user.
            top_k: Number of results to return.
            filters: Optional metadata filters.

        Returns:
            Dict with 'query', 'contexts', and 'sources' keys.
        """
        results = self.retrieve(query, top_k=top_k, filters=filters)

        contexts = []
        sources = []

        for result in results:
            section = result.metadata.get("section", "")
            act = result.metadata.get("act", "")
            source_label = f"{act} — Section {section}" if section and act else result.metadata.get("source_file", "Unknown")

            contexts.append({
                "text": result.text,
                "source": source_label,
                "score": result.score,
            })

            sources.append({
                "chunk_id": result.chunk_id,
                "source_file": result.metadata.get("source_file", ""),
                "section": section,
                "act": act,
                "score": result.score,
            })

        return {
            "query": query,
            "contexts": contexts,
            "sources": sources,
            "num_results": len(results),
        }
