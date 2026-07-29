"""
utils/document_parser.py
------------------------
Parses uploaded document files into plain text for ingestion.
Supports lightweight, dependency-friendly extraction for .txt and .pdf files.
"""

import logging
from io import BytesIO

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text content from an uploaded .txt or .pdf file.

    Args:
        file_bytes: Raw bytes from the uploaded file.
        filename: Original file name used to infer the file type.

    Returns:
        Extracted text content as a single string.

    Raises:
        ValueError: If the file type is unsupported or cannot be parsed.
    """
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension == "txt":
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("utf-8", errors="ignore")

    if extension == "pdf":
        try:
            reader = PdfReader(BytesIO(file_bytes))
            pages: list[str] = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text.strip())
            return "\n\n".join(pages)
        except Exception as exc:  # pragma: no cover - defensive broad catch
            logger.exception("Failed to parse uploaded PDF file: %s", filename)
            raise ValueError("Unable to extract text from the provided PDF file.") from exc

    raise ValueError("Unsupported file type. Please upload a .pdf or .txt file.")
