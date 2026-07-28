"""
routes/chat.py
----------------
RAG chat endpoint (protected by JWT auth).
"""

from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import answer_question
from app.utils.dependencies import get_current_user_id

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user_id: str = Depends(get_current_user_id),
) -> ChatResponse:
    """
    Runs the full Retrieval Augmented Generation pipeline:
    embeds the question, retrieves the most relevant chunks belonging
    to the current user, and asks Groq's LLM to answer using that context.
    """
    return await answer_question(payload.question, user_id)
