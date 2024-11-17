from pydantic import BaseModel


class TelegramUserBaseSchema(BaseModel):
    telegram_id: int 
    username: str 
    
    
class TelegramUserSchema(TelegramUserBaseSchema):
    id: int 
    

class TelegramUserCreateSchema(TelegramUserBaseSchema):
    pass