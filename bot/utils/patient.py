from aiogram import types

from orm.patient import get_or_create_patient_and_update_protocol
from schemas.patient import PatientCreateSchema
from keyboards.reply import (
    get_reply_keyboard,
    reply_patient_keyboard,
)
from models import Protocol


async def register_patient_or_add_protocol(
    message: types.Message,
    protocol: Protocol,
    phone_number: str,
    text: str = 'Протокол успешно добавлен! Выберите действие.'
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
    await message.answer(
        text,
        reply_markup=reply_patient_keyboard
    )
        
    return