"""
Department routes – add and list departments.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database_models.database_connection import session as SessionLocal
from database_models.department_database_model import Department as DepartmentDB
from database_models.hospital_database_model import Hospital as HospitalDB
from pydantic_models.department_model import Department
from services.admin import verify_admin
from system_prompt import system_prompt_department
from vector_database import transform_text

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/departments")
def add_department(
    department: Department,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
):
    hospital = db.query(HospitalDB).filter(HospitalDB.hospital_id == department.hospital_id).first()
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found for provided hospital_id")

    try:
        department_db = DepartmentDB(**department.model_dump())
        db.add(department_db)
        db.commit()
        db.refresh(department_db)
        merged_data = {
            "department": department.model_dump(),
            "hospital": {
                "hospital_name": hospital.hospital_name,
                "hospital_city": hospital.hospital_city,
                "hospital_area": hospital.hospital_area,
                "ownership": hospital.ownership,
                "hospital_type": hospital.hospital_type,
            },
        }
        transform_text(merged_data, system_prompt_department)
        return {"message": "Department created successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create department")


@router.get("/get_departments")
def get_departments(db: Session = Depends(get_db)):
    return db.query(DepartmentDB).all()
