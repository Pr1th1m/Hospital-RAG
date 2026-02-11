from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from database_models.base import Base

class Hospital(Base):
    __tablename__ = "hospital"
    
    hospital_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_name = Column(String, nullable=False)
    hospital_city = Column(String,nullable=False)
    hospital_area = Column(String, nullable=True)
    hospital_type = Column(String, nullable=False)
    ownership = Column(String,nullable=True)
    total_beds = Column(Integer, nullable=True)
    icu_beds = Column(Integer, nullable=True)
    emergency = Column(Boolean, nullable=False)
    accreditations = Column(ARRAY(String), nullable=True)
