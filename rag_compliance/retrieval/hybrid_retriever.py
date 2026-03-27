from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from rag_compliance.config import CHROMA_PATH
from rag_compliance.embeddings.embedder import get_embedding_function


class HybridRetriever:
    """
    Custom Hybrid Retriever that merges results from:
    - Chroma Vector Store (semantic similarity)
    - BM25 (keyword/exact match)
    and deduplicates by page_content.
    """

    def __init__(self, vector_weight: float = 0.6, bm25_weight: float = 0.4):
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

        self.db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=get_embedding_function()
        )

        self.vector_retriever = self.db.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 20, "fetch_k": 50}
        )

        self.bm25_retriever = None
        try:
            docs_dict = self.db.get()
            if docs_dict and "documents" in docs_dict and len(docs_dict["documents"]) > 0:
                documents = [
                    Document(page_content=content, metadata=meta)
                    for content, meta in zip(docs_dict["documents"], docs_dict["metadatas"])
                ]
                self.bm25_retriever = BM25Retriever.from_documents(documents)
                self.bm25_retriever.k = 20
        except Exception as e:
            print(f"Warning: Could not initialize BM25Retriever: {e}")

    def invoke(self, query: str) -> list[Document]:
        """Retrieve documents from both retrievers and merge with deduplication."""
        vector_docs = self.vector_retriever.invoke(query)

        if self.bm25_retriever:
            bm25_docs = self.bm25_retriever.invoke(query)
        else:
            bm25_docs = []

        # Merge with deduplication based on page_content
        seen = set()
        merged = []

        # Interleave: vector docs first (higher weight), then bm25
        for doc in vector_docs + bm25_docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen:
                seen.add(content_hash)
                merged.append(doc)

        return merged


def get_hybrid_retriever():
    return HybridRetriever()
