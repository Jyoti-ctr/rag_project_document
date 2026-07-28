"""
schemas/document.py
--------------------
Pydantic request/response models for document ingestion endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class DocumentPublic(BaseModel):
    id: str
    title: str
    chunk_count: int
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentPublic
    message: str = "Document ingested successfully."


class DocumentListResponse(BaseModel):
    documents: list[DocumentPublic]
    total: int
