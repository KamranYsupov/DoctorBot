from pydantic import BaseModel

from .telegram_user import TelegramUserBaseSchema


class PatientBaseSchema(TelegramUserBaseSchema):
    name: str 
    
    
class PatientSchema(PatientBaseSchema):
    id: int 
    

class PatientCreateSchema(PatientBaseSchema):
    pass