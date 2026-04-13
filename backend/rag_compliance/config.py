import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = str(BASE_DIR / "corpus_raw_v1")

# Cloud runtime defaults for a no-Docker deployment.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "complics-index")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "default")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
PINECONE_DIMENSION = int(os.getenv("PINECONE_DIMENSION", "384"))
