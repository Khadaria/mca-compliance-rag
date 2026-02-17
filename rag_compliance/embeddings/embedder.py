"""
Embedding Generator for MCA Compliance RAG system.

Wraps SentenceTransformer to generate dense vector embeddings
for document chunks and queries. Supports batch processing
with configurable model selection.
"""

import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from rag_compliance.config import get_settings

logger = logging.getLogger("rag_compliance.embeddings.embedder")


class Embedder:
    """Generates dense vector embeddings using SentenceTransformers.

    Lazy-loads the model on first use and caches it for subsequent calls.
    All embeddings are L2-normalized to enable cosine similarity via inner product.

    Args:
        model_name: SentenceTransformer model identifier. Defaults to config value.
    """

    _instance: Optional["Embedder"] = None
    _model: Optional[SentenceTransformer] = None

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dimension = settings.embedding_dimension
        logger.info("Embedder configured with model: %s", self.model_name)

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load and cache the SentenceTransformer model.

        Returns:
            Loaded SentenceTransformer model instance.
        """
        if Embedder._model is None:
            logger.info("Loading embedding model: %s ...", self.model_name)
            Embedder._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        return Embedder._model

    def embed_text(self, text: str) -> np.ndarray:
        """Generate a normalized embedding vector for a single text.

        Args:
            text: Input text to embed.

        Returns:
            1-D numpy array of shape (dimension,), L2-normalized.
        """
        model = self._get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return np.array(embedding, dtype=np.float32)

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Generate normalized embeddings for a batch of texts.

        Args:
            texts: List of input texts to embed.
            batch_size: Number of texts to process at once.

        Returns:
            2-D numpy array of shape (n_texts, dimension), L2-normalized.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        model = self._get_model()

        logger.info(
            "Embedding %d texts in batches of %d...", len(texts), batch_size
        )

        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )

        result = np.array(embeddings, dtype=np.float32)

        logger.info(
            "Generated embeddings: shape=%s, dtype=%s",
            result.shape,
            result.dtype,
        )

        return result
