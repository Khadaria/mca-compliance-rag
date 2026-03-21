import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = str(BASE_DIR / "chroma")
DATA_PATH = str(BASE_DIR / "corpus_raw_v1")

# LLM Constants
LLM_MODEL = "mistral"
EMBEDDING_MODEL = "nomic-embed-text"
