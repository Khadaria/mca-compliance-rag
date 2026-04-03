from flashrank import Ranker, RerankRequest
from langchain_core.documents import Document

class ComponentReranker:
    def __init__(self):
        # Initialize default Flashrank model (runs locally, lightweight)
        print("Initializing Flashrank model...")
        self.ranker = Ranker()
        
    def rerank(self, query: str, documents: list[Document], top_k: int = 5, min_score: float = 0.15) -> list[Document]:
        """Rerank documents and return only those above the minimum relevance score."""
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
            score = res.get("score", 0)
            print(f"  [Reranker] score={score:.4f}  text={res['text'][:80]}...")
            if score >= min_score:
                reranked_docs.append(
                    Document(page_content=res["text"], metadata=res["meta"])
                )
        
        print(f"  [Reranker] {len(reranked_docs)}/{len(results[:top_k])} passages passed min_score={min_score}")
        return reranked_docs
