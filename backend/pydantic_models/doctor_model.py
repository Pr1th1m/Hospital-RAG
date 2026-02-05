from pydantic import BaseModel, Field
from typing import List,Optional
from uuid import UUID, uuid4

class Doctor(BaseModel):
    # doctor_id: UUID = Field(default_factory=uuid4)
    # hospital_id: UUID
    doctor_name: str
    doctor_speciality: str
    doctor_experience: Optional[int] = Field(None,ge=0)
    doctor_qualifications: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    opd_timing: Optional[str] = None
    