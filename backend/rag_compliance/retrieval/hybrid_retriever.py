from langchain_community.retrievers import BM25Retriever
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from rag_compliance.config import DATA_PATH, PINECONE_API_KEY, PINECONE_INDEX, PINECONE_NAMESPACE
from rag_compliance.embeddings.embedder import get_embedding_function
from rag_compliance.ingestion.chunker import split_documents
from rag_compliance.ingestion.loader import load_and_filter_documents


class HybridRetriever:
    def __init__(self, bm25_retriever, vector_retriever, bm25_weight=0.4, vector_weight=0.6):
        self.bm25 = bm25_retriever
        self.vector = vector_retriever
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

    def _safe_retrieve(self, retriever, query):
        """
        Handles both old + new LangChain APIs
        """
        if retriever is None:
            return []

        # New LangChain
        if hasattr(retriever, "invoke"):
            return retriever.invoke(query)

        # Old LangChain
        elif hasattr(retriever, "get_relevant_documents"):
            return retriever.get_relevant_documents(query)

        else:
            raise AttributeError("Retriever has no valid retrieval method")

    def get_relevant_documents(self, query: str):
        bm25_docs = self._safe_retrieve(self.bm25, query)
        vector_docs = self._safe_retrieve(self.vector, query)

        combined = vector_docs + bm25_docs

        # Deduplicate
        seen = set()
        unique_docs = []
        for doc in combined:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                unique_docs.append(doc)

        return unique_docs

    def invoke(self, query: str):
        return self.get_relevant_documents(query)


# ✅ THIS WAS MISSING — ADD IT BACK
def get_hybrid_retriever():
    """
    Returns HybridRetriever combining:
    - Pinecone (vector search)
    - BM25 (keyword search)
    """

    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY is not set.")

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    db = PineconeVectorStore(
        index=index,
        embedding=get_embedding_function(),
        namespace=PINECONE_NAMESPACE,
        text_key="text",
    )

    vector_retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 20, "fetch_k": 50}
    )

    bm25_retriever = None

    try:
        documents = split_documents(load_and_filter_documents(DATA_PATH))
        if documents:
            bm25_retriever = BM25Retriever.from_documents(documents)
            bm25_retriever.k = 20

    except Exception as e:
        print(f"Warning: Could not initialize BM25Retriever. {e}")

    if bm25_retriever:
        return HybridRetriever(bm25_retriever, vector_retriever)

    return vector_retriever
