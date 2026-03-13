"""
Doctor routes – add and list doctors.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database_models.database_connection import session as SessionLocal
from database_models.department_database_model import Department as DepartmentDB
from database_models.doctor_database_model import Doctor as DoctorDB
from database_models.hospital_database_model import Hospital as HospitalDB
from pydantic_models.doctor_model import Doctor
from services.admin import verify_admin
from system_prompt import system_prompt_doctor
from vector_database import transform_text

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/doctors")
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
        doctor_db = DoctorDB(**doctor.model_dump())
        db.add(doctor_db)
        db.commit()
        db.refresh(doctor_db)
        merged_data = {
            "doctor": doctor.model_dump(),
            "hospital": {
                "hospital_name": hospital.hospital_name,
                "hospital_city": hospital.hospital_city,
                "ownership": hospital.ownership,
                "has_emergency": hospital.emergency,
            },
            "department": {
                "department_name": department.department_name,
                "icu_support": department.icu_support,
            },
        }
        transform_text(merged_data, system_prompt_doctor)
        return {"message": "Doctor created successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create doctor")


@router.get("/get_doctors")
def get_doctors(db: Session = Depends(get_db)):
    return db.query(DoctorDB).all()
