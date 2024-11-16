from typing import Optional, List, Dict
from datetime import date, time 

from pydantic import BaseModel, Field

from .patient import PatientSchema
from web.patients.models import Patient
from web.doctors.models import Doctor


class ProtocolBaseSchema(BaseModel):
    patient_name: str
    drugs: List[str]
    first_take: date
    last_take: date
    time_to_take: time
    reception_calendar: Dict
    notificatons_calendar: Dict
    

class ProtocolSchema(ProtocolBaseSchema):
    id: int
    patient: PatientSchema
    
    
class ProtocolCreateSchema(ProtocolBaseSchema):
    patient_id: Optional[int] = Field(title='ID Пациента', default=None)
    doctor_id: int
    


    