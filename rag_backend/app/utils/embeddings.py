"""
utils/embeddings.py
--------------------
Loads the SentenceTransformer embedding model exactly once (singleton)
and exposes helpers to embed text and compute cosine similarity.
"""

import logging
import math

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Singleton wrapper around the SentenceTransformer model."""

    _instance: SentenceTransformer | None = None

    @classmethod
    def get_instance(cls) -> SentenceTransformer:
        if cls._instance is None:
            logger.info("Loading embedding model '%s' (one-time load)...", settings.EMBEDDING_MODEL_NAME)
            cls._instance = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded successfully.")
        return cls._instance


def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a single piece of text."""
    model = EmbeddingModel.get_instance()
    vector = model.encode(text, convert_to_numpy=True, normalize_embeddings=False)
    return vector.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for a batch of texts (more efficient)."""
    if not texts:
        return []
    model = EmbeddingModel.get_instance()
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
    return vectors.tolist()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def preload_model() -> None:
    """Explicitly triggers model loading. Call this during app startup."""
    EmbeddingModel.get_instance()
