"""
routes/document.py
--------------------
Document ingestion endpoints (protected by JWT auth).
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.schemas.document import DocumentListResponse, DocumentUploadResponse
from app.services.document_service import delete_document, list_documents, upload_document_from_file
from app.utils.dependencies import get_current_user_id

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload(
    title: str = Form(default=""),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> DocumentUploadResponse:
    """
    Accepts a PDF or TXT file upload, extracts its text, chunks it,
    generates embeddings, and persists everything to MongoDB.
    """
    file_bytes = await file.read()
    document = await upload_document_from_file(
        file_bytes=file_bytes,
        filename=file.filename or "uploaded_file",
        title=title,
        user_id=user_id,
    )
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
