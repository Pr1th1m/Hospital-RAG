from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_models.hospital_model import Hospital
from pydantic_models.doctor_model import Doctor
from pydantic_models.department_model import Department
app = FastAPI()

@app.get("/")
def home():
    return {"message": "backend Intigrated"}

@app.post('/hospitals')
def add_hospital(hospital:Hospital):
    if hospital:
        return hospital
    return {"message": "Hospital not created"}

@app.post('/doctors')
def add_doctor(doctor:Doctor):
    if doctor:
        return doctor
    return {"message": "Doctor not created"}

@app.post('/departments')
def add_department(department:Department):
    if department:
        return department   
    return {"message": "Department not created"}    

