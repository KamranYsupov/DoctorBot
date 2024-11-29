import uuid

import loguru
from aiogram import types, F, Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from asgiref.sync import sync_to_async

from keyboards.inline import get_inline_keyboard
from keyboards.reply import (
    reply_keyboard_remove,
    get_reply_keyboard,
    reply_patient_keyboard,
    reply_doctor_keyboard
)
from schemas.doctor import DoctorCreateSchema
from orm.telegram_user import get_doctor_or_patient
from utils.patient import register_patient_or_add_protocol
from models import Doctor, Protocol
from .state import DoctorState, PatientState

router = Router()


async def cancel_handler(
    message: types.Message,
    state: FSMContext,
    telegram_id: int,
):
    telegram_user = await get_doctor_or_patient(telegram_id)
    reply_markup = reply_patient_keyboard
    
    if not telegram_user:
        reply_markup = reply_keyboard_remove
    elif isinstance(telegram_user, Doctor):
        reply_markup = reply_doctor_keyboard

    message_data = {'text': 'Действие отменено'}
    
    try:
        await message.edit_text(**message_data)
    except TelegramBadRequest:
        message_data['reply_markup'] = reply_markup
        await message.answer(**message_data)
        
    await state.clear()
    

@router.callback_query(
    StateFilter('*'),
    (F.data == 'cancel')
)
async def cancel_callback_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    await cancel_handler(
        message=callback.message,
        state=state,
        telegram_id=callback.from_user.id
    )


@router.message(
    StateFilter('*'),
    or_f(Command('cancel'), (F.text.lower() == 'отмена ❌'))
)
async def cancel_message_handler(
    message: types.Message,
    state: FSMContext,
):
    await cancel_handler(
        message=message,
        state=state,
        telegram_id=message.from_user.id
    )


@router.message(DoctorState.fio, F.text)
async def register_doctor(message: types.Message, state: FSMContext):
    fio = message.text
    if len(fio) > 150:
        return await message.answer('Длина не должна превышать 150 символов')
    
    doctor_create_schema = DoctorCreateSchema(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        fio=fio
    )
    await Doctor.objects.acreate(**doctor_create_schema.model_dump())
    await message.answer(
        'Регистрация прошла успешно! Выберите действие.',
        reply_markup=get_reply_keyboard(
            buttons=('Меню 📁', 'Старт нового протокола 📝')
        )
    )
    
    await state.clear()
    
    
@router.message(PatientState.phone_number, F.contact)
async def register_patient(
    message: types.Message,
    state: FSMContext
):
    state_data = await state.get_data()
    protocol_id = state_data['protocol_id']
    protocol = await Protocol.objects.aget(id=protocol_id)
    
    if protocol.patient_id:
        await message.answer(
            'Протокол уже добавлен другим пользователем',
            reply_markup=reply_keyboard_remove,
        )
        return
        
    
    await register_patient_or_add_protocol(
        message=message,
        protocol=protocol,
        phone_number=message.contact.phone_number
    )
        
    
    await state.clear()
    