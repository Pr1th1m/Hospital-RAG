from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from database_models.base import Base

class Department(Base):
    __tablename__ = "department"

    department_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospital.hospital_id"), nullable=False)
    department_name = Column(String, nullable=False)
    services = Column(ARRAY(String),nullable=True)
    icu_support = Column(Boolean, nullable=False)
