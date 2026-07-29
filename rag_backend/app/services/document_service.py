"""
services/document_service.py
------------------------------
Business logic for document ingestion:
  store document -> chunk text -> generate embeddings -> store chunks.
"""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.database import get_chunks_collection, get_documents_collection
from app.schemas.document import DocumentPublic, DocumentUploadRequest
from app.utils.chunking import chunk_text
from app.utils.document_parser import extract_text_from_file
from app.utils.embeddings import embed_texts


async def upload_document(payload: DocumentUploadRequest, user_id: str) -> DocumentPublic:
    """
    Ingests a new document for the given user:
      1. Persist the raw document.
      2. Split its content into chunks.
      3. Generate embeddings for all chunks in a single batch call.
      4. Persist each chunk with its embedding.
    """
    documents_collection = get_documents_collection()
    chunks_collection = get_chunks_collection()

    created_at = datetime.now(timezone.utc)

    document_doc = {
        "user_id": user_id,
        "title": payload.title,
        "content": payload.content,
        "created_at": created_at,
    }
    doc_result = await documents_collection.insert_one(document_doc)
    document_id = str(doc_result.inserted_id)

    text_chunks = chunk_text(payload.content)
    if not text_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content is empty after chunking.",
        )

    embeddings = embed_texts(text_chunks)

    chunk_docs = [
        {
            "document_id": document_id,
            "user_id": user_id,
            "chunk_number": index,
            "content": chunk_content,
            "embedding": embedding,
        }
        for index, (chunk_content, embedding) in enumerate(zip(text_chunks, embeddings))
    ]

    if chunk_docs:
        await chunks_collection.insert_many(chunk_docs)

    return DocumentPublic(
        id=document_id,
        title=payload.title,
        chunk_count=len(chunk_docs),
        created_at=created_at,
    )


async def upload_document_from_file(
    file_bytes: bytes,
    filename: str,
    title: str,
    user_id: str,
) -> DocumentPublic:
    """Ingests an uploaded .txt or .pdf file for the given user."""
    documents_collection = get_documents_collection()
    chunks_collection = get_chunks_collection()

    created_at = datetime.now(timezone.utc)

    try:
        extracted_text = extract_text_from_file(file_bytes, filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse the uploaded document.",
        ) from exc

    if not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extracted document text is empty.",
        )

    normalized_title = (title or filename.rsplit(".", 1)[0]).strip() or "Uploaded document"

    document_doc = {
        "user_id": user_id,
        "title": normalized_title,
        "content": extracted_text,
        "created_at": created_at,
    }

    try:
        doc_result = await documents_collection.insert_one(document_doc)
        document_id = str(doc_result.inserted_id)

        text_chunks = chunk_text(extracted_text)
        if not text_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document content is empty after chunking.",
            )

        embeddings = embed_texts(text_chunks)

        chunk_docs = [
            {
                "document_id": document_id,
                "user_id": user_id,
                "chunk_number": index,
                "content": chunk_content,
                "embedding": embedding,
            }
            for index, (chunk_content, embedding) in enumerate(zip(text_chunks, embeddings))
        ]

        if chunk_docs:
            await chunks_collection.insert_many(chunk_docs)

        return DocumentPublic(
            id=document_id,
            title=normalized_title,
            chunk_count=len(chunk_docs),
            created_at=created_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        await documents_collection.delete_one({"_id": doc_result.inserted_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest the uploaded document.",
        ) from exc


async def list_documents(user_id: str) -> list[DocumentPublic]:
    """Returns all documents belonging to the given user, most recent first."""
    documents_collection = get_documents_collection()
    chunks_collection = get_chunks_collection()

    cursor = documents_collection.find({"user_id": user_id}).sort("created_at", -1)
    documents: list[DocumentPublic] = []

    async for doc in cursor:
        chunk_count = await chunks_collection.count_documents({"document_id": str(doc["_id"])})
        documents.append(
            DocumentPublic(
                id=str(doc["_id"]),
                title=doc["title"],
                chunk_count=chunk_count,
                created_at=doc["created_at"],
            )
        )

    return documents


async def delete_document(document_id: str, user_id: str) -> None:
    """Deletes a document and all of its associated chunks (must belong to user_id)."""
    documents_collection = get_documents_collection()
    chunks_collection = get_chunks_collection()

    try:
        object_id = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document id.")

    document = await documents_collection.find_one({"_id": object_id, "user_id": user_id})
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    await chunks_collection.delete_many({"document_id": document_id})
    await documents_collection.delete_one({"_id": object_id})
