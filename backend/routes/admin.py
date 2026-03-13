"""
Admin routes – login and reindex vector store.
"""

import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import ADMIN_PASSWORD, ADMIN_TOKEN_TTL_MINUTES
from database_models.database_connection import session as SessionLocal
from database_models.department_database_model import Department as DepartmentDB
from database_models.doctor_database_model import Doctor as DoctorDB
from database_models.hospital_database_model import Hospital as HospitalDB
from services.admin import _issue_admin_token, verify_admin
from system_prompt import system_prompt_hospital, system_prompt_department, system_prompt_doctor
from vector_database import transform_text

log = logging.getLogger(__name__)

router = APIRouter()


class AdminLogin(BaseModel):
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/admin/login")
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


@router.post("/admin/reindex_vector_store")
def reindex_vector_store(db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    hospitals = db.query(HospitalDB).all()
    departments = db.query(DepartmentDB).all()
    doctors = db.query(DoctorDB).all()

    indexed = {"hospitals": 0, "departments": 0, "doctors": 0}
    errors = []

    for h in hospitals:
        try:
            transform_text(h, system_prompt_hospital)
            indexed["hospitals"] += 1
        except Exception as e:
            log.warning("Vector indexing failed for hospital: %s", e)
            errors.append(f"hospital {getattr(h, 'hospital_name', '?')}: {e}")

    for d in departments:
        try:
            transform_text(d, system_prompt_department)
            indexed["departments"] += 1
        except Exception as e:
            log.warning("Vector indexing failed for department: %s", e)
            errors.append(f"department {getattr(d, 'department_name', '?')}: {e}")

    for doc in doctors:
        try:
            transform_text(doc, system_prompt_doctor)
            indexed["doctors"] += 1
        except Exception as e:
            log.warning("Vector indexing failed for doctor: %s", e)
            errors.append(f"doctor {getattr(doc, 'doctor_name', '?')}: {e}")

    resp = {"message": "Reindex request completed.", "indexed": indexed}
    if errors:
        resp["errors"] = errors
    return resp
