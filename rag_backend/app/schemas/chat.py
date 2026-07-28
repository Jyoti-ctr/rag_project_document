"""
schemas/chat.py
----------------
Pydantic request/response models for the RAG chat endpoint.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class RetrievedChunk(BaseModel):
    document_id: str
    chunk_number: int
    content: str
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    retrieved_context: list[RetrievedChunk]
    question: str
