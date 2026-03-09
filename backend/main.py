from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from pydantic_models.hospital_model import Hospital
from pydantic_models.doctor_model import Doctor
from pydantic_models.department_model import Department
from database_models.database_connection import session, engine
from database_models.hospital_database_model import Hospital as HospitalDB
from database_models.doctor_database_model import Doctor as DoctorDB
from database_models.department_database_model import Department as DepartmentDB
from database_models.base import Base
from vector_database import transform_text
from system_prompt import system_prompt_hospital,system_prompt_department,system_prompt_doctor,system_prompt_hospital_list,system_prompt_department_list,system_prompt_doctor_list
from tavily import TavilyClient
from vector_database import vector_store
from pydantic_models.chatmodel import ChatRequest, chat_sessions
from app import system_prompt1
from groq_client import client, call_with_fallback
import json
import uuid
import os
import hashlib
import secrets
from dotenv import load_dotenv

load_dotenv()

tavilyclient = TavilyClient(
    api_key=os.getenv('TAVILY_API_KEY')
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Admin Auth ---
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
admin_tokens: set = set()

class AdminLogin(BaseModel):
    password: str

def verify_admin(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    if token not in admin_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

@app.post("/admin/login")
def admin_login(login: AdminLogin):
    if login.password == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        admin_tokens.add(token)
        return {"token": token, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "backend Intigrated"}

@app.post('/hospitals')
def add_hospital(hospital:Hospital, db:Session = Depends(get_db)):
    if hospital:
        db.add(HospitalDB(**hospital.model_dump()))
        db.commit()
        # transform_text(hospital,system_prompt_hospital)
        return {"message": "Hospital created successfully"}
    return {"message": "Hospital details not found"}

@app.post('/departments')
def add_department(department:Department, db:Session = Depends(get_db)):
    if department:
        hospital = db.query(HospitalDB).filter(
        HospitalDB.hospital_id == department.hospital_id
        ).first()
        print('hospital: ',hospital.__dict__)
        print('department: ',department)
        print('merged:\n',hospital.__dict__ | department.__dict__)
        department_merged = hospital.__dict__ | department.__dict__
        db.add(DepartmentDB(**department.model_dump()))
        db.commit()
        # transform_text(department_merged,system_prompt_department)
        return {"message": f"Department \n{department}\n created successfully"}   
    return {"message": "Department details not found"}    

@app.post('/doctors')
def add_doctor(doctor:Doctor, db:Session = Depends(get_db)):
    if doctor:
        hospital = db.query(HospitalDB).filter(
        HospitalDB.hospital_id == doctor.hospital_id
        ).first()
        department = db.query(DepartmentDB).filter(
        DepartmentDB.department_id == doctor.department_id
        ).first()
        print('merged:\n',hospital.__dict__ | department.__dict__ | doctor.__dict__)
        doctor_merged = hospital.__dict__ | department.__dict__ | doctor.__dict__
        db.add(DoctorDB(**doctor.model_dump()))
        db.commit()
        # transform_text(doctor_merged,system_prompt_doctor)
        return {"message": f"Doctor \n{doctor}\n created successfully"}
    return {"message": "Doctor details not found"}

@app.get('/get_hospitals')
def get_hospitals(db:Session = Depends(get_db)):
    hospitals = db.query(HospitalDB).all()
    return hospitals

@app.get('/get_departments')
def get_departments(db:Session = Depends(get_db)):
    departments = db.query(DepartmentDB).all()
    return departments

@app.get('/get_doctors')
def get_doctors(db:Session = Depends(get_db)):
    doctors = db.query(DoctorDB).all()
    return doctors

def websearch(query:str):
    print('tool calling....')
    responses = tavilyclient.search(query)
    result = "\n\n".join(
        response["content"] for response in responses["results"]
    )
    return result

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "active_sessions": len(chat_sessions),
    }

@app.post('/transcribe')
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        transcription = call_with_fallback(
            lambda c: c.audio.transcriptions.create(
                model='whisper-large-v3-turbo',
                file=(file.filename, audio_bytes),
                response_format='text'
            )
        )
        return {'text': transcription.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Transcription failed: {str(e)}')

@app.post('/chat')
def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    print(session_id)
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [
            {
                'role': 'system',
                'content': system_prompt1
            }
        ]
    messages = chat_sessions[session_id]
    chunks = vector_store.similarity_search(request.message, 20)
    content = "\n\n".join([c.page_content for c in chunks])

    if content:
        user_query = f"Question: {request.message}\nrelevant context: {content}\nIMPORTANT: List ALL matching results from the context, do not omit any.\nAnswer:"
    else:
        user_query = f"Question: {request.message}"

    messages.append({
        'role': 'user',
        'content': user_query.strip()
    })

    try:
        while True:
            completion = call_with_fallback(
                lambda c: c.chat.completions.create(
                    temperature=0.2,
                    model='openai/gpt-oss-120b',
                    # model='llama-3.3-70b-versatile',
                    messages=messages,
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "websearch",
                                "description": "Search the internet for real-time, up-to-date information. Use this tool when the user asks about weather, news, current events, live scores, stock prices, or any question that is NOT answered by the retrieved database context.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The search query to perform search on."
                                        }
                                    },
                                    "required": ["query"],
                                }
                            }
                        }
                    ],
                    tool_choice='auto',
                )
            )
            messages.append(completion.choices[0].message)
            toolcalls = completion.choices[0].message.tool_calls

            if not toolcalls:
                answer = completion.choices[0].message.content
                chat_sessions[session_id] = messages
                return {'session_id': session_id, 'answer': answer}
            else:
                for tool in toolcalls:
                    funcname = tool.function.name
                    funcparams = tool.function.arguments

                    if funcname == 'websearch':
                        args = json.loads(funcparams)
                        toolResult = websearch(args['query'])

                        messages.append({
                            'role': 'tool',
                            'tool_call_id': tool.id,
                            'name': funcname,
                            'content': toolResult
                        })
    except Exception as e:
        error_str = str(e).lower()
        if any(kw in error_str for kw in ['rate', 'limit', '429', 'quota', 'exceeded']):
            return {
                'session_id': session_id,
                'answer': '⏳ I\'m currently experiencing high demand. Please wait a moment and try again.'
            }
        raise HTTPException(status_code=500, detail=f'Chat failed: {str(e)}')


@app.post('/chat/stream')
def chat_stream(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [
            {'role': 'system', 'content': system_prompt1}
        ]
    messages = chat_sessions[session_id]
    chunks = vector_store.similarity_search(request.message, 20)
    content = "\n\n".join([c.page_content for c in chunks])

    if content:
        user_query = f"Question: {request.message}\nrelevant context: {content}\nIMPORTANT: List ALL matching results from the context, do not omit any.\nAnswer:"
    else:
        user_query = f"Question: {request.message}"

    messages.append({'role': 'user', 'content': user_query.strip()})

    def event_generator():
        try:
            # Handle tool calls in a loop (non-streamed)
            while True:
                completion = call_with_fallback(
                    lambda c: c.chat.completions.create(
                        temperature=0.2,
                        model='openai/gpt-oss-120b',
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
                                                "description": "The search query."
                                            }
                                        },
                                        "required": ["query"],
                                    }
                                }
                            }
                        ],
                        tool_choice='auto',
                    )
                )
                toolcalls = completion.choices[0].message.tool_calls

                if not toolcalls:
                    # No tool calls — use the answer we already have
                    answer = completion.choices[0].message.content or ""
                    # Stream it word-by-word for typewriter effect
                    words = answer.split(' ')
                    for i, word in enumerate(words):
                        token = word if i == 0 else ' ' + word
                        yield f"data: {json.dumps({'token': token})}\n\n"

                    messages.append({'role': 'assistant', 'content': answer})
                    chat_sessions[session_id] = messages
                    yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
                    return

                # Process tool calls
                messages.append(completion.choices[0].message)
                for tool in toolcalls:
                    if tool.function.name == 'websearch':
                        args = json.loads(tool.function.arguments)
                        tool_result = websearch(args['query'])
                        messages.append({
                            'role': 'tool',
                            'tool_call_id': tool.id,
                            'name': tool.function.name,
                            'content': tool_result
                        })

        except Exception as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ['rate', 'limit', '429', 'quota', 'exceeded']):
                yield f"data: {json.dumps({'token': '⏳ I am currently experiencing high demand. Please wait a moment and try again.'})}\n\n"
            else:
                yield f"data: {json.dumps({'token': '⚠️ Something went wrong. Please try again.'})}\n\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')