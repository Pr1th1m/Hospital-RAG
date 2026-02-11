from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
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

Base.metadata.create_all(bind=engine)

app = FastAPI()

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