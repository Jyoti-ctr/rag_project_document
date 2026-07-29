"""
utils/embeddings.py
--------------------
Generates text embeddings using Hugging Face's Free Serverless Inference API.
This requires ZERO local memory (no PyTorch/SentenceTransformers needed in RAM),
making it perfect for Render's 512 MB free tier.
"""

import logging
import math
import requests

from app.config import settings

logger = logging.getLogger(__name__)

# Free Hugging Face Inference API Endpoint for sentence-transformers
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"


def _get_headers() -> dict:
    """Build request headers with optional API authorization token."""
    headers = {"Content-Type": "application/json"}
    
    # Check for HF_TOKEN or GROQ_API_KEY in settings if available
    hf_token = getattr(settings, "HF_TOKEN", None) or getattr(settings, "GROQ_API_KEY", "")
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    return headers


def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a single string via Hugging Face API."""
    if not text:
        return []

    try:
        response = requests.post(
            HF_API_URL,
            headers=_get_headers(),
            json={"inputs": [text], "options": {"wait_for_model": True}},
            timeout=30,
        )
        
        if response.status_code != 200:
            logger.error("HF API Error (%d): %s", response.status_code, response.text)
            raise RuntimeError(f"HuggingFace API returned status {response.status_code}")

        result = response.json()
        
        # Format check for API response structure
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list):
                return result[0]
            return result

        logger.error("Unexpected response format from HF API: %s", result)
        raise ValueError("Invalid embedding vector format returned")

    except Exception as err:
        logger.exception("Failed to generate embedding for text: %s", err)
        raise err


def embed_texts(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    """Generate embedding vectors for a list of texts in small batches.
    
    Processing in batches prevents request payload limits during large PDF uploads.
    """
    if not texts:
        return []

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = requests.post(
                HF_API_URL,
                headers=_get_headers(),
                json={"inputs": batch, "options": {"wait_for_model": True}},
                timeout=60,
            )

            if response.status_code != 200:
                logger.error("HF API Batch Error (%d): %s", response.status_code, response.text)
                raise RuntimeError(f"HuggingFace API batch call failed with status {response.status_code}")

            batch_results = response.json()
            
            if isinstance(batch_results, list):
                all_embeddings.extend(batch_results)
            else:
                logger.error("Unexpected batch response structure: %s", batch_results)
                raise ValueError("Invalid batch embedding vectors format returned")

        except Exception as err:
            logger.exception("Failed to generate batch embeddings: %s", err)
            raise err

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
    logger.info("Using cloud API for embeddings; skipping local model load.")