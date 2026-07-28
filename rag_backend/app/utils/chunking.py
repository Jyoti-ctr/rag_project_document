"""
utils/chunking.py
------------------
Simple, dependency-free text chunking with configurable size and overlap.
Splits on whitespace-delimited words to avoid cutting words in half.
"""

from app.config import settings


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[str]:
    """
    Splits `text` into overlapping chunks of roughly `chunk_size` characters.

    Args:
        text: The full document content.
        chunk_size: Max characters per chunk (defaults to settings.CHUNK_SIZE).
        chunk_overlap: Overlap in characters between consecutive chunks
                       (defaults to settings.CHUNK_OVERLAP).

    Returns:
        A list of non-empty text chunks.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    text = text.strip()
    if not text:
        return []

    words = text.split()
    chunks: list[str] = []
    current_words: list[str] = []
    current_len = 0

    for word in words:
        current_words.append(word)
        current_len += len(word) + 1  # +1 for the space

        if current_len >= chunk_size:
            chunk_str = " ".join(current_words)
            chunks.append(chunk_str)

            # Build overlap: keep trailing words whose combined length
            # is approximately chunk_overlap characters.
            overlap_words: list[str] = []
            overlap_len = 0
            for w in reversed(current_words):
                overlap_len += len(w) + 1
                overlap_words.insert(0, w)
                if overlap_len >= chunk_overlap:
                    break

            current_words = overlap_words
            current_len = sum(len(w) + 1 for w in current_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
