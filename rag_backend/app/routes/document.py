"""
routes/document.py
--------------------
Document ingestion endpoints (protected by JWT auth).
"""

from fastapi import APIRouter, Depends, status

from app.schemas.document import (
    DocumentListResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.services.document_service import delete_document, list_documents, upload_document
from app.utils.dependencies import get_current_user_id

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload(
    payload: DocumentUploadRequest,
    user_id: str = Depends(get_current_user_id),
) -> DocumentUploadResponse:
    """
    Ingests a new document: stores it, chunks the content, generates
    embeddings for each chunk, and persists everything to MongoDB.
    """
    document = await upload_document(payload, user_id)
    return DocumentUploadResponse(document=document)


@router.get("", response_model=DocumentListResponse)
async def list_all(user_id: str = Depends(get_current_user_id)) -> DocumentListResponse:
    """Lists all documents belonging to the current authenticated user."""
    documents = await list_documents(user_id)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(document_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    """Deletes a document and all of its chunks."""
    await delete_document(document_id, user_id)
