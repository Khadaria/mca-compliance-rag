import os
from rag_compliance.config import EMBEDDING_PROVIDER, EMBEDDING_MODEL


def get_embedding_function():
    provider = EMBEDDING_PROVIDER

    if provider == "sentence_transformers":
        from langchain_huggingface import HuggingFaceEmbeddings
        # local_files_only=True: use cached model, don't try to contact huggingface.co
        # The model was already downloaded during populate_database.py
        return HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"local_files_only": True}
        )

    else:
        # Default: Ollama (for local development only)
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=EMBEDDING_MODEL)
