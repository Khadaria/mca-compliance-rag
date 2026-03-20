from langchain_ollama import OllamaEmbeddings
from rag_compliance.config import EMBEDDING_MODEL

def get_embedding_function():
    return OllamaEmbeddings(model=EMBEDDING_MODEL)
