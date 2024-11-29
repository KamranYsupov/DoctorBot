from typing import Optional, List

from pydantic import BaseModel, Field

from .patient import PatientSchema
from .doctor import DoctorSchema
from .drug import DrugSchema, DrugCreateSchema
    
    
class ProtocolBaseSchema(BaseModel):
    patient_name: str
    

class ProtocolSchema(ProtocolBaseSchema):
    id: str
    drugs: List[DrugSchema]
    doctor: DoctorSchema
    patient: Optional[PatientSchema]
    
    
class ProtocolCreateSchema(ProtocolBaseSchema):
    patient_ulid: str
    patient_id: Optional[str] = Field(title='ID Пациента', default=None)
    doctor_id: str
    drugs: Optional[List[DrugCreateSchema]] = Field(
        title='Список препаратов',
        default=set()
    )
    
    

    


    