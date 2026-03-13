"""
Health and utility routes – health check and audio transcription.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from database_models.database_connection import session as SessionLocal
from groq_client import call_with_fallback
from pydantic_models.chatmodel import chat_sessions
from services.admin import admin_tokens, _cleanup_expired_tokens

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    _cleanup_expired_tokens()
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "active_sessions": len(chat_sessions),
        "active_admin_tokens": len(admin_tokens),
    }


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        transcription = call_with_fallback(
            lambda c: c.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=(file.filename, audio_bytes),
                response_format="text",
            )
        )
        return {"text": transcription.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
