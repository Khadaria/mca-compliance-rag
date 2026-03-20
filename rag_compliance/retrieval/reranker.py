from flashrank import Ranker, RerankRequest
from langchain_core.documents import Document

class ComponentReranker:
    def __init__(self):
        # Initialize default Flashrank model (runs locally, lightweight)
        print("Initializing Flashrank model...")
        self.ranker = Ranker()
        
    def rerank(self, query: str, documents: list[Document], top_k: int = 5) -> list[Document]:
        if not documents:
            return []
            
        passages = [
            {
                "id": i, 
                "text": doc.page_content, 
                "meta": doc.metadata
            }
            for i, doc in enumerate(documents)
        ]
        
        request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(request)
        
        reranked_docs = []
        for res in results[:top_k]:
            reranked_docs.append(
                Document(page_content=res["text"], metadata=res["meta"])
            )
            
        return reranked_docs
