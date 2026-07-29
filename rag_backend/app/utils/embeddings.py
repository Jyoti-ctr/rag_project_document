"""
utils/embeddings.py
--------------------
Generates text embeddings using Hugging Face's official InferenceClient SDK.
Using the official SDK eliminates raw HTTP connection/DNS resolution issues
while requiring ZERO PyTorch memory on Render.
"""

import logging
import math
from huggingface_hub import InferenceClient
from app.config import settings

logger = logging.getLogger(__name__)

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


def _get_client() -> InferenceClient:
    """Initialize HuggingFace InferenceClient with auth token."""
    token = getattr(settings, "HF_TOKEN", None) or getattr(settings, "GROQ_API_KEY", None)
    return InferenceClient(model=MODEL_ID, token=token)


def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a single string via HF SDK."""
    if not text:
        return []

    try:
        client = _get_client()
        embedding = client.feature_extraction(text)

        # Normalize structure into a 1D list of floats
        if isinstance(embedding, list) and len(embedding) > 0:
            if isinstance(embedding[0], list):
                return [float(x) for x in embedding[0]]
            return [float(x) for x in embedding]

        return [float(x) for x in embedding]

    except Exception as err:
        logger.exception("HF SDK Embedding Error: %s", err)
        # Safe zero-vector fallback to prevent 500 Internal Server Error
        return [0.0] * 384


def embed_texts(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    """Generate embedding vectors for a list of strings in batches."""
    if not texts:
        return []

    all_embeddings = []
    client = _get_client()

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            results = client.feature_extraction(batch)
            if isinstance(results, list):
                for item in results:
                    if isinstance(item, list):
                        all_embeddings.append([float(x) for x in item])
                    else:
                        all_embeddings.append([float(x) for x in item])
            else:
                all_embeddings.extend([[0.0] * 384 for _ in batch])
        except Exception as err:
            logger.exception("HF SDK Batch Embedding Error: %s", err)
            all_embeddings.extend([[0.0] * 384 for _ in batch])

    return all_embeddings


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def preload_model() -> None:
    """No local model preloading required for API-based embeddings."""
    logger.info("Using HuggingFace Inference SDK; skipping local model load.")