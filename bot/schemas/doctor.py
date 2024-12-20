from pydantic import BaseModel

from .telegram_user import TelegramUserBaseSchema


class DoctorBaseSchema(TelegramUserBaseSchema):
    fio: str 
    
    
class DoctorSchema(DoctorBaseSchema):
    id: str 
    

class DoctorCreateSchema(DoctorBaseSchema):
    pass