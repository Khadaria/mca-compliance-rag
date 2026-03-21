from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document

from rag_compliance.config import CHROMA_PATH
from rag_compliance.embeddings.embedder import get_embedding_function

def get_hybrid_retriever():
    """
    Returns an EnsembleRetriever combining:
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
                for content, meta in zip(docs_dict["documents"], docs_dict["metadatas"])
            ]
            bm25_retriever = BM25Retriever.from_documents(documents)
            bm25_retriever.k = 20
    except Exception as e:
        print(f"Warning: Could not initialize BM25Retriever. Database might be empty. {e}")

    if bm25_retriever:
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.4, 0.6]
        )
        return ensemble_retriever
        
    return vector_retriever
