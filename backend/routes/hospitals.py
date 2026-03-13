"""
Hospital routes – add and list hospitals.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database_models.database_connection import session as SessionLocal
from database_models.hospital_database_model import Hospital as HospitalDB
from pydantic_models.hospital_model import Hospital
from services.admin import verify_admin
from system_prompt import system_prompt_hospital
from vector_database import transform_text

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/hospitals")
def add_hospital(
    hospital: Hospital,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
):
    try:
        hospital_db = HospitalDB(**hospital.model_dump())
        db.add(hospital_db)
        db.commit()
        db.refresh(hospital_db)
        transform_text(hospital, system_prompt_hospital)
        return {"message": "Hospital created successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create hospital")


@router.get("/get_hospitals")
def get_hospitals(db: Session = Depends(get_db)):
    return db.query(HospitalDB).all()
