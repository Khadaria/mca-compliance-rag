from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from rag_compliance.config import CHROMA_PATH
from rag_compliance.embeddings.embedder import get_embedding_function


class HybridRetriever:
    def __init__(self, bm25_retriever, vector_retriever, bm25_weight=0.4, vector_weight=0.6):
        self.bm25 = bm25_retriever
        self.vector = vector_retriever
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

    def get_relevant_documents(self, query):
        bm25_docs = self.bm25.get_relevant_documents(query)
        vector_docs = self.vector.get_relevant_documents(query)

        # Combine results
        combined = []

        # Add weighted results (simple version)
        combined.extend(vector_docs)
        combined.extend(bm25_docs)

        # Remove duplicates
        seen = set()
        unique_docs = []
        for doc in combined:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                unique_docs.append(doc)

        return unique_docs


def get_hybrid_retriever():
    """
    Returns a HybridRetriever combining:
    - Chroma Vector Store (Semantic Search)
    - BM25 (Keyword Search)
    """

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function()
    )

    vector_retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 20, "fetch_k": 50}
    )

    bm25_retriever = None

    try:
        docs_dict = db.get()

        if docs_dict and "documents" in docs_dict and len(docs_dict["documents"]) > 0:
            documents = [
                Document(page_content=content, metadata=meta)
                for content, meta in zip(
                    docs_dict["documents"], docs_dict["metadatas"]
                )
            ]

            bm25_retriever = BM25Retriever.from_documents(documents)
            bm25_retriever.k = 20

    except Exception as e:
        print(f"Warning: Could not initialize BM25Retriever. {e}")

    # ✅ Return hybrid if possible
    if bm25_retriever:
        return HybridRetriever(bm25_retriever, vector_retriever)

    # ✅ Fallback
    return vector_retriever
