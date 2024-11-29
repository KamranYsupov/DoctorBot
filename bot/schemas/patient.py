from pydantic import BaseModel

from .telegram_user import TelegramUserBaseSchema


class PatientBaseSchema(TelegramUserBaseSchema):
    name: str
    phone_number: str 
    
    
class PatientSchema(PatientBaseSchema):
    id: str 
    

class PatientCreateSchema(PatientBaseSchema):
    pass