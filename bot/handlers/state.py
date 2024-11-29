from aiogram.fsm.state import StatesGroup, State

    
class DoctorState(StatesGroup):
    fio = State()
    

class PatientState(StatesGroup):
    protocol_id = State()
    phone_number = State()


class CreateProtocolState(StatesGroup):
    patient_name = State()
    drug_name = State()
    first_take = State()
    period = State()
    time_to_take = State()
    
    drugs = State()
    

class EditProtocolState(StatesGroup):
    protocol_id = State()
    drugs = State()
    first_take = State()
    period = State()
    time_to_take = State()