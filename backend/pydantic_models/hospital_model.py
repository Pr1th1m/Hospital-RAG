from pydantic import BaseModel, Field
from typing import List,Optional
from uuid import UUID, uuid4

class Hospital(BaseModel):
    # hospital_id: UUID = Field(default_factory=uuid4)#unique id of the hospital
    hospital_name: str                              #name of the hospital
    hospital_city: str                              #city of the hospital
    hospital_area: Optional[str] = None             #area of the hospital
    hospital_type: str                              #multispeciality,single speciality
    ownership: Optional[str] = None                 #government,private
    total_beds: Optional[int] = Field(None,ge=0)    #total number of beds
    icu_beds: Optional[int] = Field(None,ge=0)      #number of icu beds
    emergency: bool                                 #has emergency services
    accreditations: Optional[List[str]] = []        #list of accreditations
    
