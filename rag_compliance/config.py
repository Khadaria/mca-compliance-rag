"""
Configuration module for the MCA Compliance RAG system.

Loads settings from environment variables and .env file using Pydantic BaseSettings.
All configuration is centralized here to ensure consistency across modules.
"""

import logging
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide configuration loaded from environment variables."""

    # ── Paths ──────────────────────────────────────────────────────────
    corpus_dir: str = "corpus_raw_v1"
    vector_store_dir: str = "vector_store"

    # ── Embedding ──────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # Must match the model output dimension

    # ── LLM Provider ───────────────────────────────────────────────────
    llm_provider: Literal["gemini", "ollama"] = "gemini"

    # Gemini (free tier via Google AI Studio)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Ollama (fully local, no API key)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # ── Retrieval ──────────────────────────────────────────────────────
    top_k: int = 5
    retrieval_score_threshold: float = 0.25

    # ── Chunking ───────────────────────────────────────────────────────
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # ── Logging ────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── API ─────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure and return the application logger.

    Args:
        level: Optional log level override. Defaults to settings.log_level.

    Returns:
        Configured root logger for the rag_compliance package.
    """
    settings = get_settings()
    log_level = level or settings.log_level

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("rag_compliance")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    return logger
