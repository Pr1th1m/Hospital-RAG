from pydantic import BaseModel, Field
from typing import List,Optional
from uuid import UUID, uuid4


class Department(BaseModel):
    # department_id: UUID = Field(default_factory=uuid4)
    hospital_id: UUID
    department_name: str    # cardiology,neurology,orthopedics,etc
    services: Optional[List[str]] = []
    icu_support: bool
    