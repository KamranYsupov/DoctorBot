from aiogram import types

from orm.patient import get_or_create_patient_and_update_protocol
from schemas.patient import PatientCreateSchema
from keyboards.reply import (
    get_reply_keyboard,
    reply_patient_keyboard,
)
from models import Protocol, Doctor


async def register_patient_or_add_protocol(
    message: types.Message,
    protocol: Protocol,
    phone_number: str,
    text: str | None = None 
) -> None:
    patient_create_schema = PatientCreateSchema(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        phone_number=phone_number,
        name=protocol.patient_name
    )    
    await get_or_create_patient_and_update_protocol(
        protocol, 
        patient_create_schema
    )
    if not text:
        doctor = await Doctor.objects.aget(id=protocol.doctor_id)
        text = (
        f'Дорогой(ая) {protocol.patient_name}, это Доктор бот,'
        f'доктор {doctor.fio} назначил вам протокол.\n' 
        'Чтобы повысить результативность лечения,  вам будут приходить напоминая.\n\n'
        'За 15, 5 и 1 минуту до времени приема вам будут направлены  сообщения с напоминанием.\n'
        'За 1 минуту до приема вам поступит вызов от голосового помощника с напоминанием.\n\n'
        'Как только вы выполнили предписание врача обязательно отметьте это в боте.'
    )
        
    await message.answer(
        text,
        reply_markup=reply_patient_keyboard
    )
        
    return