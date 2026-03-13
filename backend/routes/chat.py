"""
Chat routes – /chat and /chat/stream endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database_models.database_connection import session as SessionLocal
from pydantic_models.chatmodel import ChatRequest
from services.chat_service import handle_chat, handle_chat_stream

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    return handle_chat(request.message, request.session_id, db)


@router.post("/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    return handle_chat_stream(request.message, request.session_id, db)
