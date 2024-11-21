from aiogram.fsm.state import StatesGroup, State


class BaseProtocolState(StatesGroup):
    drugs = State()
    first_take = State()
    period = State()
    time_to_take = State()
    
    
class CreateProtocolState(BaseProtocolState):
    patient_name = State()
    

class EditProtocolState(BaseProtocolState):
    protocol_id = State()