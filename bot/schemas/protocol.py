from typing import Optional, List

from pydantic import BaseModel, Field

from .patient import PatientSchema
from .doctor import DoctorSchema
from .drug import DrugSchema, DrugCreateSchema
    
    
class ProtocolBaseSchema(BaseModel):
    patient_name: str
    

class ProtocolSchema(ProtocolBaseSchema):
    id: int
    drugs: List[DrugSchema]
    doctor: DoctorSchema
    patient: Optional[PatientSchema]
    
    
class ProtocolCreateSchema(ProtocolBaseSchema):
    patient_id: Optional[int] = Field(title='ID Пациента', default=None)
    doctor_id: int
    drugs: Optional[List[DrugCreateSchema]] = Field(
        title='Список препаратов',
        default=set()
    )
    
    

    


    