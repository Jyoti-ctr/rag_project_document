"""
services/chat_service.py
--------------------------
Business logic for the RAG chat pipeline:
  embed question -> retrieve user chunks -> cosine similarity ->
  top-K chunks -> build context -> call Groq -> return answer.
"""

import logging

from fastapi import HTTPException, status
from groq import APIError, Groq

from app.config import settings
from app.database import get_chunks_collection
from app.schemas.chat import ChatResponse, RetrievedChunk
from app.utils.embeddings import cosine_similarity, embed_text

logger = logging.getLogger(__name__)

_groq_client: Groq | None = None


def get_groq_client() -> Groq:
    """Lazily instantiate a singleton Groq client."""
    global _groq_client
    if _groq_client is None:
        if not settings.GROQ_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GROQ_API_KEY is not configured on the server.",
            )
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


async def retrieve_top_chunks(question: str, user_id: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """
    Embeds the question, loads all chunks belonging to the user, scores
    them by cosine similarity, and returns the top_k most relevant chunks.
    """
    top_k = top_k or settings.TOP_K_CHUNKS
    chunks_collection = get_chunks_collection()

    question_embedding = embed_text(question)

    scored_chunks: list[RetrievedChunk] = []
    cursor = chunks_collection.find({"user_id": user_id})

    async for chunk in cursor:
        score = cosine_similarity(question_embedding, chunk["embedding"])
        scored_chunks.append(
            RetrievedChunk(
                document_id=chunk["document_id"],
                chunk_number=chunk["chunk_number"],
                content=chunk["content"],
                similarity_score=round(score, 4),
            )
        )

    scored_chunks.sort(key=lambda c: c.similarity_score, reverse=True)
    return scored_chunks[:top_k]


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Concatenates retrieved chunks into a single context block for the LLM prompt."""
    return "\n\n".join(f"[Chunk {c.chunk_number}] {c.content}" for c in chunks)


async def generate_answer(question: str, context: str) -> str:
    """Calls the Groq chat completion API with the retrieved context and question."""
    client = get_groq_client()

    system_prompt = (
        "You are a helpful assistant that answers questions strictly using the "
        "provided context. If the answer cannot be found in the context, say so "
        "honestly instead of making something up."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return completion.choices[0].message.content or ""
    except APIError as exc:
        logger.exception("Groq API call failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Groq API error: {exc}",
        )


async def answer_question(question: str, user_id: str) -> ChatResponse:
    """Full RAG pipeline orchestration for a single chat turn."""
    top_chunks = await retrieve_top_chunks(question, user_id)

    if not top_chunks:
        return ChatResponse(
            answer="I don't have any documents to reference yet. Please upload a document first.",
            retrieved_context=[],
            question=question,
        )

    context = build_context(top_chunks)
    answer = await generate_answer(question, context)

    return ChatResponse(
        answer=answer,
        retrieved_context=top_chunks,
        question=question,
    )
