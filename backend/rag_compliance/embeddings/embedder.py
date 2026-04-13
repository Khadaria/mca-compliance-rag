from rag_compliance.config import EMBEDDING_MODEL


def get_embedding_function():
    from langchain_huggingface import HuggingFaceEmbeddings

    # Allow the host to download the model on first build/startup.
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
