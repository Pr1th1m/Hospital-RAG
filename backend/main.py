from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import system_prompt1
from database_models.base import Base
from database_models.database_connection import engine, session
from database_models.department_database_model import Department as DepartmentDB
from database_models.doctor_database_model import Doctor as DoctorDB
from database_models.hospital_database_model import Hospital as HospitalDB
from groq_client import call_with_fallback
from pydantic_models.chatmodel import ChatRequest, chat_sessions
from pydantic_models.department_model import Department
from pydantic_models.doctor_model import Doctor
from pydantic_models.hospital_model import Hospital
from tavily import TavilyClient
from vector_database import vector_store

import hmac
import json
import os
import re
import secrets
import uuid


load_dotenv()


# Retrieval defaults can be tuned through env without code changes.
RETRIEVAL_TOP_K = max(1, int(os.getenv("RETRIEVAL_TOP_K", "8")))
ADMIN_TOKEN_TTL_MINUTES = max(5, int(os.getenv("ADMIN_TOKEN_TTL_MINUTES", "120")))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# In-memory token store: {token: expiration_utc}
admin_tokens: Dict[str, datetime] = {}


def _issue_admin_token() -> str:
    token = secrets.token_hex(32)
    admin_tokens[token] = datetime.now(timezone.utc) + timedelta(minutes=ADMIN_TOKEN_TTL_MINUTES)
    return token


def _cleanup_expired_tokens() -> None:
    now = datetime.now(timezone.utc)
    expired = [token for token, expires_at in admin_tokens.items() if expires_at <= now]
    for token in expired:
        admin_tokens.pop(token, None)


def _infer_entity_type(query: str) -> Optional[str]:
    lowered = query.lower()
    if any(keyword in lowered for keyword in ["doctor", "doctors", "dr.", "physician", "specialist"]):
        return "doctor"
    if any(keyword in lowered for keyword in ["department", "departments", "cardiology", "orthopedic", "neurology"]):
        return "department"
    if any(keyword in lowered for keyword in ["hospital", "hospitals", "clinic", "medical center"]):
        return "hospital"
    return None


def _is_realtime_web_query(message: str) -> bool:
    lowered = message.lower()
    realtime_keywords = [
        "weather",
        "temp",
        "temperature",
        "forecast",
        "rain",
        "humidity",
        "news",
        "headlines",
        "stock",
        "price",
        "crypto",
        "score",
        "match",
        "today",
        "now",
        "current",
    ]
    healthcare_keywords = ["hospital", "hospitals", "doctor", "doctors", "department", "departments", "clinic"]

    has_realtime_signal = any(keyword in lowered for keyword in realtime_keywords)
    has_healthcare_signal = any(keyword in lowered for keyword in healthcare_keywords)
    return has_realtime_signal and not has_healthcare_signal


def retrieve_relevant_chunks(query: str):
    entity_type = _infer_entity_type(query)

    if entity_type:
        filtered_chunks = vector_store.similarity_search(
            query,
            k=RETRIEVAL_TOP_K,
            filter={"entity_type": entity_type},
        )
        if filtered_chunks:
            return filtered_chunks

    return vector_store.similarity_search(query, k=RETRIEVAL_TOP_K)


def build_grounded_user_query(message: str, content: str) -> str:
    if content:
        return (
            f"Question: {message}\n"
            f"relevant context: {content}\n"
            "Instructions: Answer only from the relevant context above. "
            "If the answer is not present, clearly say that the requested information is not available in the current data.\n"
            "Answer:"
        )

    return (
        f"Question: {message}\n"
        "Instructions: No relevant local context was retrieved. "
        "If this is about hospitals, departments, or doctors in local data, say it is not available. "
        "Use websearch only for real-time or general web information.\n"
        "Answer:"
    )


def _extract_city_hospital_query(message: str) -> Optional[str]:
    lowered = message.strip().lower()
    if "hospital" not in lowered:
        return None

    patterns = [
        r"\bhospitals?\s+in\s+([a-zA-Z][a-zA-Z\s\-.']+)$",
        r"\bhospitals?\s+at\s+([a-zA-Z][a-zA-Z\s\-.']+)$",
        r"\blist\s+hospitals?\s+in\s+([a-zA-Z][a-zA-Z\s\-.']+)$",
        r"\bshow\s+hospitals?\s+in\s+([a-zA-Z][a-zA-Z\s\-.']+)$",
        r"\bwhich\s+hospitals?\s+are\s+in\s+([a-zA-Z][a-zA-Z\s\-.']+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            city = match.group(1).strip(" .!?")
            return city.title()
    return None


def _build_city_hospital_answer(city: str, db: Session) -> Optional[str]:
    hospitals = (
        db.query(HospitalDB)
        .filter(HospitalDB.hospital_city.ilike(city))
        .order_by(HospitalDB.hospital_name.asc())
        .all()
    )

    if not hospitals:
        hospitals = (
            db.query(HospitalDB)
            .filter(HospitalDB.hospital_city.ilike(f"%{city}%"))
            .order_by(HospitalDB.hospital_name.asc())
            .all()
        )

    if not hospitals:
        return None

    lines = [f"Here are the hospitals in **{city}** from current data:"]
    for hospital in hospitals:
        area_part = f" ({hospital.hospital_area})" if hospital.hospital_area else ""
        lines.append(f"- **{hospital.hospital_name}**{area_part}")

    lines.append(f"Total: **{len(hospitals)}** hospitals.")
    return "\n".join(lines)


def _build_realtime_answer(message: str) -> str:
    search_result = websearch(message)
    if not search_result or not search_result.strip():
        return "I could not fetch live web results right now. Please try again in a moment."

    try:
        completion = call_with_fallback(
            lambda c: c.chat.completions.create(
                temperature=0.2,
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You summarize web search results accurately and concisely. "
                            "Answer the user question using only the provided web results. "
                            "If exact value is unavailable, say so clearly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question: {message}\n\nWeb search results:\n{search_result}\n\nAnswer:",
                    },
                ],
            )
        )
        return completion.choices[0].message.content or "I could not produce a reliable live answer right now."
    except Exception:
        return "I could not produce a reliable live answer right now."


tavily_api_key = os.getenv("TAVILY_API_KEY")
tavilyclient = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AdminLogin(BaseModel):
    password: str


def verify_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    _cleanup_expired_tokens()
    token = authorization.replace("Bearer ", "", 1).strip()
    expires_at = admin_tokens.get(token)
    if not expires_at:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if expires_at <= datetime.now(timezone.utc):
        admin_tokens.pop(token, None)
        raise HTTPException(status_code=401, detail="Session expired")

    return token


@app.post("/admin/login")
def admin_login(login: AdminLogin):
    if not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Admin login is not configured. Set ADMIN_PASSWORD in environment.",
        )

    if hmac.compare_digest(login.password, ADMIN_PASSWORD):
        token = _issue_admin_token()
        return {"token": token, "message": "Login successful", "expires_in_minutes": ADMIN_TOKEN_TTL_MINUTES}

    raise HTTPException(status_code=401, detail="Invalid password")


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "backend Integrated"}


@app.post("/hospitals")
def add_hospital(
    hospital: Hospital,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
):
    try:
        db.add(HospitalDB(**hospital.model_dump()))
        db.commit()
        return {"message": "Hospital created successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create hospital")


@app.post("/departments")
def add_department(
    department: Department,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
):
    hospital = db.query(HospitalDB).filter(HospitalDB.hospital_id == department.hospital_id).first()
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found for provided hospital_id")

    try:
        db.add(DepartmentDB(**department.model_dump()))
        db.commit()
        return {"message": "Department created successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create department")


@app.post("/doctors")
def add_doctor(
    doctor: Doctor,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
):
    hospital = db.query(HospitalDB).filter(HospitalDB.hospital_id == doctor.hospital_id).first()
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found for provided hospital_id")

    department = db.query(DepartmentDB).filter(DepartmentDB.department_id == doctor.department_id).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found for provided department_id")

    if department.hospital_id != doctor.hospital_id:
        raise HTTPException(
            status_code=400,
            detail="department_id does not belong to the provided hospital_id",
        )

    try:
        db.add(DoctorDB(**doctor.model_dump()))
        db.commit()
        return {"message": "Doctor created successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create doctor")


@app.get("/get_hospitals")
def get_hospitals(db: Session = Depends(get_db)):
    return db.query(HospitalDB).all()


@app.get("/get_departments")
def get_departments(db: Session = Depends(get_db)):
    return db.query(DepartmentDB).all()


@app.get("/get_doctors")
def get_doctors(db: Session = Depends(get_db)):
    return db.query(DoctorDB).all()


def websearch(query: str):
    print('Tool calling...')
    if tavilyclient is None:
        return "Web search is currently unavailable."

    responses = tavilyclient.search(query)
    return "\n\n".join(response["content"] for response in responses.get("results", []))


@app.get("/health")
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


@app.post("/transcribe")
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


@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [{"role": "system", "content": system_prompt1}]

    messages = chat_sessions[session_id]

    city = _extract_city_hospital_query(request.message)
    if city:
        direct_answer = _build_city_hospital_answer(city, db)
        if direct_answer:
            messages.append({"role": "user", "content": request.message.strip()})
            messages.append({"role": "assistant", "content": direct_answer})
            chat_sessions[session_id] = messages
            return {"session_id": session_id, "answer": direct_answer}

    if _is_realtime_web_query(request.message):
        realtime_answer = _build_realtime_answer(request.message)
        messages.append({"role": "user", "content": request.message.strip()})
        messages.append({"role": "assistant", "content": realtime_answer})
        chat_sessions[session_id] = messages
        return {"session_id": session_id, "answer": realtime_answer}

    chunks = retrieve_relevant_chunks(request.message)
    content = "\n\n".join([c.page_content for c in chunks])
    user_query = build_grounded_user_query(request.message, content)

    messages.append({"role": "user", "content": user_query.strip()})

    try:
        while True:
            completion = call_with_fallback(
                lambda c: c.chat.completions.create(
                    temperature=0.2,
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "websearch",
                                "description": "Search the internet for real-time, up-to-date information. Use this tool for weather, news, current events, live scores, stock prices, or questions not answerable from retrieved context.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The search query to perform search on.",
                                        }
                                    },
                                    "required": ["query"],
                                },
                            },
                        }
                    ],
                    tool_choice="auto",
                )
            )
            messages.append(completion.choices[0].message)
            toolcalls = completion.choices[0].message.tool_calls

            if not toolcalls:
                answer = completion.choices[0].message.content
                chat_sessions[session_id] = messages
                return {"session_id": session_id, "answer": answer}

            for tool in toolcalls:
                funcname = tool.function.name
                funcparams = tool.function.arguments

                if funcname == "websearch":
                    args = json.loads(funcparams)
                    tool_result = websearch(args["query"])
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool.id,
                            "name": funcname,
                            "content": tool_result,
                        }
                    )
    except Exception as e:
        error_str = str(e).lower()
        if any(kw in error_str for kw in ["rate", "limit", "429", "quota", "exceeded"]):
            return {
                "session_id": session_id,
                "answer": "I am currently experiencing high demand. Please wait a moment and try again.",
            }
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [{"role": "system", "content": system_prompt1}]

    messages = chat_sessions[session_id]

    city = _extract_city_hospital_query(request.message)
    if city:
        direct_answer = _build_city_hospital_answer(city, db)
        if direct_answer:
            messages.append({"role": "user", "content": request.message.strip()})
            messages.append({"role": "assistant", "content": direct_answer})
            chat_sessions[session_id] = messages

            def direct_event_generator():
                words = direct_answer.split(" ")
                for i, word in enumerate(words):
                    token = word if i == 0 else " " + word
                    yield f"data: {json.dumps({'token': token})}\\n\\n"
                yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\\n\\n"

            return StreamingResponse(direct_event_generator(), media_type="text/event-stream")

    if _is_realtime_web_query(request.message):
        realtime_answer = _build_realtime_answer(request.message)
        messages.append({"role": "user", "content": request.message.strip()})
        messages.append({"role": "assistant", "content": realtime_answer})
        chat_sessions[session_id] = messages

        def realtime_event_generator():
            words = realtime_answer.split(" ")
            for i, word in enumerate(words):
                token = word if i == 0 else " " + word
                yield f"data: {json.dumps({'token': token})}\\n\\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\\n\\n"

        return StreamingResponse(realtime_event_generator(), media_type="text/event-stream")

    chunks = retrieve_relevant_chunks(request.message)
    content = "\n\n".join([c.page_content for c in chunks])
    user_query = build_grounded_user_query(request.message, content)
    messages.append({"role": "user", "content": user_query.strip()})

    def event_generator():
        try:
            while True:
                completion = call_with_fallback(
                    lambda c: c.chat.completions.create(
                        temperature=0.2,
                        model="openai/gpt-oss-120b",
                        messages=messages,
                        tools=[
                            {
                                "type": "function",
                                "function": {
                                    "name": "websearch",
                                    "description": "Search the internet for real-time, up-to-date information.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "The search query.",
                                            }
                                        },
                                        "required": ["query"],
                                    },
                                },
                            }
                        ],
                        tool_choice="auto",
                    )
                )
                toolcalls = completion.choices[0].message.tool_calls

                if not toolcalls:
                    answer = completion.choices[0].message.content or ""
                    words = answer.split(" ")
                    for i, word in enumerate(words):
                        token = word if i == 0 else " " + word
                        yield f"data: {json.dumps({'token': token})}\\n\\n"

                    messages.append({"role": "assistant", "content": answer})
                    chat_sessions[session_id] = messages
                    yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\\n\\n"
                    return

                messages.append(completion.choices[0].message)
                for tool in toolcalls:
                    if tool.function.name == "websearch":
                        args = json.loads(tool.function.arguments)
                        tool_result = websearch(args["query"])
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool.id,
                                "name": tool.function.name,
                                "content": tool_result,
                            }
                        )

        except Exception as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ["rate", "limit", "429", "quota", "exceeded"]):
                token = "I am currently experiencing high demand. Please wait a moment and try again."
            else:
                token = "Something went wrong. Please try again."

            yield f"data: {json.dumps({'token': token})}\\n\\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
