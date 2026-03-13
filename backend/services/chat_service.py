"""
Chat service – orchestrates retrieval, LLM calls, web search, and streaming.
"""

import json
import re
import uuid
from typing import Optional

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from system_prompt import system_prompt1
from groq_client import call_with_fallback
from pydantic_models.chatmodel import chat_sessions
from database_models.hospital_database_model import Hospital as HospitalDB
from services.retrieval import retrieve_relevant_chunks, has_local_data, build_grounded_user_query
from services.web_search import websearch


# ── Helpers ──────────────────────────────────────────────────────────

def _is_realtime_web_query(message: str) -> bool:
    lowered = message.lower()
    realtime_keywords = [
        "weather", "temp", "temperature", "forecast", "rain", "humidity",
        "news", "headlines", "stock", "price", "crypto",
        "score", "match", "today", "now", "current",
    ]
    healthcare_keywords = [
        "hospital", "hospitals", "doctor", "doctors",
        "department", "departments", "clinic",
    ]

    has_realtime_signal = any(keyword in lowered for keyword in realtime_keywords)
    has_healthcare_signal = any(keyword in lowered for keyword in healthcare_keywords)
    return has_realtime_signal and not has_healthcare_signal


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


# ── LLM tool definition (shared) ────────────────────────────────────

_WEBSEARCH_TOOL = {
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


# ── Non-streaming chat ───────────────────────────────────────────────

def handle_chat(message: str, session_id: Optional[str], db: Session) -> dict:
    session_id = session_id or str(uuid.uuid4())
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [{"role": "system", "content": system_prompt1}]

    messages = chat_sessions[session_id]

    # City-hospital shortcut
    city = _extract_city_hospital_query(message)
    if city:
        direct_answer = _build_city_hospital_answer(city, db)
        if direct_answer:
            messages.append({"role": "user", "content": message.strip()})
            messages.append({"role": "assistant", "content": direct_answer})
            chat_sessions[session_id] = messages
            return {"session_id": session_id, "answer": direct_answer}

    # Real-time web query
    if _is_realtime_web_query(message):
        realtime_answer = _build_realtime_answer(message)
        messages.append({"role": "user", "content": message.strip()})
        messages.append({"role": "assistant", "content": realtime_answer})
        chat_sessions[session_id] = messages
        return {"session_id": session_id, "answer": realtime_answer}

    # RAG retrieval
    chunks = retrieve_relevant_chunks(message)
    if not has_local_data(chunks):
        realtime_answer = _build_realtime_answer(message)
        messages.append({"role": "user", "content": message.strip()})
        messages.append({"role": "assistant", "content": realtime_answer})
        chat_sessions[session_id] = messages
        return {"session_id": session_id, "answer": realtime_answer}

    content = "\n\n".join([c.page_content for c in chunks])
    user_query = build_grounded_user_query(message, content)
    messages.append({"role": "user", "content": user_query.strip()})

    try:
        while True:
            completion = call_with_fallback(
                lambda c: c.chat.completions.create(
                    temperature=0.2,
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    tools=[_WEBSEARCH_TOOL],
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
            return {
                "session_id": session_id,
                "answer": "I am currently experiencing high demand. Please wait a moment and try again.",
            }
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ── Streaming chat ───────────────────────────────────────────────────

def handle_chat_stream(message: str, session_id: Optional[str], db: Session) -> StreamingResponse:
    session_id = session_id or str(uuid.uuid4())
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [{"role": "system", "content": system_prompt1}]

    messages = chat_sessions[session_id]

    # City-hospital shortcut
    city = _extract_city_hospital_query(message)
    if city:
        direct_answer = _build_city_hospital_answer(city, db)
        if direct_answer:
            messages.append({"role": "user", "content": message.strip()})
            messages.append({"role": "assistant", "content": direct_answer})
            chat_sessions[session_id] = messages

            def direct_event_generator():
                words = direct_answer.split(" ")
                for i, word in enumerate(words):
                    token = word if i == 0 else " " + word
                    yield f"data: {json.dumps({'token': token})}\n\n"
                yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

            return StreamingResponse(direct_event_generator(), media_type="text/event-stream")

    # Real-time web query
    if _is_realtime_web_query(message):
        realtime_answer = _build_realtime_answer(message)
        messages.append({"role": "user", "content": message.strip()})
        messages.append({"role": "assistant", "content": realtime_answer})
        chat_sessions[session_id] = messages

        def realtime_event_generator():
            words = realtime_answer.split(" ")
            for i, word in enumerate(words):
                token = word if i == 0 else " " + word
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

        return StreamingResponse(realtime_event_generator(), media_type="text/event-stream")

    # RAG retrieval
    chunks = retrieve_relevant_chunks(message)
    if not has_local_data(chunks):
        realtime_answer = _build_realtime_answer(message)
        messages.append({"role": "user", "content": message.strip()})
        messages.append({"role": "assistant", "content": realtime_answer})
        chat_sessions[session_id] = messages

        def realtime_fallback_event_generator():
            words = realtime_answer.split(" ")
            for i, word in enumerate(words):
                token = word if i == 0 else " " + word
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

        return StreamingResponse(realtime_fallback_event_generator(), media_type="text/event-stream")

    content = "\n\n".join([c.page_content for c in chunks])
    user_query = build_grounded_user_query(message, content)
    messages.append({"role": "user", "content": user_query.strip()})

    def event_generator():
        try:
            while True:
                completion = call_with_fallback(
                    lambda c: c.chat.completions.create(
                        temperature=0.2,
                        model="openai/gpt-oss-120b",
                        messages=messages,
                        tools=[_WEBSEARCH_TOOL],
                        tool_choice="auto",
                    )
                )
                toolcalls = completion.choices[0].message.tool_calls

                if not toolcalls:
                    answer = completion.choices[0].message.content or ""
                    words = answer.split(" ")
                    for i, word in enumerate(words):
                        token = word if i == 0 else " " + word
                        yield f"data: {json.dumps({'token': token})}\n\n"

                    messages.append({"role": "assistant", "content": answer})
                    chat_sessions[session_id] = messages
                    yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
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

            yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
