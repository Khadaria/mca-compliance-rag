import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = str(BASE_DIR / "chroma")
DATA_PATH = str(BASE_DIR / "corpus_raw_v1")

# LLM Provider: "groq", "gemini", or "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Ollama settings (local only)
LLM_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Embedding: "sentence_transformers" or "ollama"
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")