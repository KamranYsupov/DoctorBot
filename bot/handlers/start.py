import loguru
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command, CommandObject
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

from .fio import DoctorState
from schemas.patient import PatientCreateSchema
from keyboards.reply import (
    reply_cancel_keyboard,
    get_reply_keyboard,
    reply_patient_keyboard,
    reply_doctor_keyboard
)
from orm.patient import get_or_create_patient_and_update_protocol
from orm.telegram_user import get_doctor_or_patient
from web.protocols.models import Protocol
from web.patients.models import Patient
from web.doctors.models import Doctor

router = Router()


@router.message(CommandStart())
async def start_command_handler(
    message: types.Message,
    command: CommandObject,
    state: FSMContext,
):
    
    telegram_user = await get_doctor_or_patient(telegram_id=message.from_user.id)
    message_text = 'Вы уже зарегистрированы. Выберите действие.'
    
    if not telegram_user:
        pass
    elif isinstance(telegram_user, Doctor):
        await message.answer(
            message_text,
            reply_markup=reply_doctor_keyboard
        )
        return
    elif isinstance(telegram_user, Patient) and not command.args:
        await message.answer(
            message_text,
            reply_markup=reply_patient_keyboard
        )
        return
    
    message_text = f'Привет, {message.from_user.first_name}.'

    if not command.args:
        message_text += '\nОтправь свое ФИО одним сообщением'
        
        await message.answer(
            message_text,
            reply_markup=reply_cancel_keyboard,
        )
        await state.set_state(DoctorState.fio)
        return
    
    
    protocol_id = command.args
        
    try:
        protocol = await Protocol.objects.aget(id=protocol_id)
    except ObjectDoesNotExist:
        await message.answer('Неправильный QR-код')
        return 
        
    patient_create_schema = PatientCreateSchema(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        name=protocol.patient_name
    )
    await get_or_create_patient_and_update_protocol(
        protocol, 
        patient_create_schema
    )
            
    await message.answer(
        'Протокол успешно добавлен! Выберите действие.',
        reply_markup=reply_patient_keyboard
    )

    
    

