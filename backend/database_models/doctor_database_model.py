from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from database_models.base import Base


class Doctor(Base):
    __tablename__ = "doctor"

    doctor_id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True),ForeignKey("hospital.hospital_id"),nullable=False)
    department_id = Column(UUID(as_uuid=True),ForeignKey("department.department_id"),nullable=False)
    doctor_name = Column(String,nullable=False)
    doctor_speciality = Column(String, nullable=False)
    doctor_experience = Column(Integer,nullable=True)
    doctor_qualifications = Column(ARRAY(String), nullable=True)
    languages = Column(ARRAY(String), nullable=True)
    opd_timing = Column(String, nullable=True)