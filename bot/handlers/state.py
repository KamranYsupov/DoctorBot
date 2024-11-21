from aiogram.fsm.state import StatesGroup, State

    
class CreateProtocolState(StatesGroup):
    patient_name = State()
    drugs = State()
    first_take = State()
    period = State()
    time_to_take = State()
    

class EditProtocolState(StatesGroup):
    protocol_id = State()
    drugs = State()
    first_take = State()
    period = State()
    time_to_take = State()