from fastapi import FastAPI, Depends
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
from groq import Groq
from tavily import TavilyClient
from vector_database import vector_store
import json
import uuid
import os
from dotenv import load_dotenv
from pydantic_models.chatmodel import ChatRequest,chat_sessions
from app import system_prompt1

load_dotenv()
Base.metadata.create_all(bind=engine)

client = Groq(
    api_key = os.getenv('GROQ_API_KEY')
)

tavilyclient = TavilyClient(
    api_key = os.getenv('TAVILY_API_KEY')
)

app = FastAPI()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

def websearch(query:dict):
    print('tool calling....')
    responses = tavilyclient.search(query)
    result = "\n\n".join(
        response["content"] for response in responses["results"]
    )
    return result


@app.get("/health")
def health(db: Session = Depends(get_db)):
    # Check database connectivity
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
    hosp = []
    hospitals = db.query(HospitalDB).all()
    for hospital in hospitals:
        hosp.append(str(hospital.__dict__))
    transform_text(str(hosp),system_prompt_hospital_list)
    return hospitals

@app.get('/get_departments')
def get_departments(db:Session = Depends(get_db)):
    dept = []
    departments = db.query(DepartmentDB).all()
    for department in departments:
        hospital = db.query(HospitalDB).filter(
            HospitalDB.hospital_id == department.hospital_id
        ).first()
        dept.append(str(department.__dict__ | hospital.__dict__))
    transform_text(str(dept),system_prompt_department_list)
    return departments

@app.get('/get_doctors')
def get_doctors(db:Session = Depends(get_db)):
    docs = []
    doctors = db.query(DoctorDB).all()
    for doctor in doctors:
        hospital = db.query(HospitalDB).filter(
            HospitalDB.hospital_id == doctor.hospital_id
        ).first()
        department = db.query(DepartmentDB).filter(
            DepartmentDB.department_id == doctor.department_id
        ).first()
        docs.append(str(doctor.__dict__ | hospital.__dict__ | department.__dict__))
    for doc in docs:
        transform_text(str(doc),system_prompt_doctor_list)
    return {"Message": "Doctors fetched successfully"}

@app.post('/chat')
def chat(request: ChatRequest):
    # Auto-generate a unique session ID for new users
    session_id = request.session_id or str(uuid.uuid4())
    print(session_id)
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [
            {
                'role': 'system',
                'content': system_prompt1
            }
        ]
    print(chat_sessions[session_id])
    messages = chat_sessions[session_id]
    chunks = vector_store.similarity_search(request.message,7)
    content = "\n\n".join([c.page_content for c in chunks])

    if content :
        user_query = f"Question: {request.message}\nrelevant context: {content}\nAnswer:"
    else:
        user_query = f"Question: {request.message}"

    messages.append({
        'role': 'user',
        'content': user_query.strip()
    })

    while True:
        completion = client.chat.completions.create(
            temperature = 0,
            model = 'openai/gpt-oss-120b',
            # model = 'llama-3.3-70b-versatile',
            messages = messages,
            tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "websearch",
                            "description": "Search the latest information and realtime data from the internet.",
                            "parameters": {
                            # JSON Schema object
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
            tool_choice = 'auto',
        )
        # print('Assistant: ',completion.choices[0].message.content)
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
                    toolResult = websearch(funcparams)

                    messages.append({
                        'role': 'tool',
                        'tool_call_id':tool.id,
                        'name':funcname,
                        'content':toolResult
                    })









