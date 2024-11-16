from typing import Optional, List
from datetime import time 

from pydantic import BaseModel, Field

from .patient import PatientSchema
from web.patients.models import Patient
from web.doctors.models import Doctor


class ProtocolBaseSchema(BaseModel):
    patient_name: str
    drugs: List[str]
    first_take: str
    period: int
    time_to_take: time
    

class ProtocolSchema(ProtocolBaseSchema):
    id: int
    patient: PatientSchema
    
    
class ProtocolCreateSchema(ProtocolBaseSchema):
    patient_id: Optional[int] = Field(title='ID Пациента', default=None)
    doctor_id: int
    


    