from typing import Optional, List, Dict
from datetime import date, time 

from pydantic import BaseModel, Field


class DrugBaseSchema(BaseModel):
    name: str
    first_take: date
    last_take: date
    time_to_take: time
    reception_calendar: Dict
    notifications_calendar: Dict
    
    
class DrugSchema(DrugBaseSchema):
    id: str
    
    
class DrugCreateSchema(DrugBaseSchema):
    pass