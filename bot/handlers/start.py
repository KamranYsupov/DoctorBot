import loguru
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command, CommandObject
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

from .state import DoctorState, PatientState
from schemas.patient import PatientCreateSchema
from keyboards.reply import (
    reply_cancel_keyboard,
    get_reply_keyboard,
    reply_patient_keyboard,
    reply_doctor_keyboard,
    get_reply_contact_keyboard
)
from orm.patient import get_or_create_patient_and_update_protocol
from orm.telegram_user import get_doctor_or_patient
from utils.patient import register_patient_or_add_protocol
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
        
    
    
    if isinstance(telegram_user, Patient):
        await register_patient_or_add_protocol(
            message=message,
            protocol=protocol,
            phone_number=telegram_user.phone_number
        )
        return
    
    button_text = 'Отправить номер телефона 📲'
    await message.answer(
        'Протокол найден ✅.\nДля завершения регистрации '
        f'нажми на кнопу <b><em>"{button_text}"</em></b>, '
        'чтобы его отправить.\n\n'
        'На него будет приходить вызов во время приёма лекарств',
        reply_markup=get_reply_contact_keyboard(button_text),
        parse_mode='HTML',
    )
    await state.update_data(protocol_id=protocol.id)
    await state.set_state(PatientState.phone_number)
    
    
    
    

    
    

