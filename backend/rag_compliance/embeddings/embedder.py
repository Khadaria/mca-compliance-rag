import os
from rag_compliance.config import EMBEDDING_PROVIDER, EMBEDDING_MODEL


def get_embedding_function():
    provider = EMBEDDING_PROVIDER

    if provider == "sentence_transformers":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    else:
        # Default: Ollama (for local development only)
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=EMBEDDING_MODEL)
