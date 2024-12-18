import uuid
import calendar
from datetime import datetime, date, time, timedelta

import loguru
from aiogram import types, F, Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asgiref.sync import sync_to_async
from django.utils import timezone

from core import config
from keyboards.inline import (
    get_inline_keyboard, 
    get_protocol_inline_button_keyboard,
    inline_cancel_keyboard
)
from keyboards.reply import (
    reply_keyboard_remove, 
    reply_cancel_keyboard,
    get_reply_keyboard,
    reply_calendar_keyboard,
    reply_doctor_keyboard,
)
from utils.validators import (
    valdate_string_from_message,
    valdate_first_take_from_message,
    valdate_period_from_message,
    valdate_time_to_take_from_message,
    validate_drugs,
)
from schemas.doctor import DoctorCreateSchema
from schemas.protocol import ProtocolCreateSchema
from utils.validators import get_integer_from_string
from utils.protocol import (
    get_timedelta_calendar,
    send_edit_protocol_notification_to_patient
)
from utils.message import default_process_time_to_take_message
from models import Drug, Doctor, Protocol
from .state import EditDrugState

router = Router()


@router.callback_query(F.data.startswith('edit_drugs_'))
async def edit_drug_name_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    drug_id = callback.data.split('_')[-1]
    
    await state.update_data(drug_id=drug_id)
    
    await callback.message.delete()
    await callback.message.answer(
        'Отправьте новое название препарата',
        reply_markup=reply_cancel_keyboard,
        parse_mode='HTML',
    )    
   
    await state.set_state(EditDrugState.name)
    
    
@router.message(EditDrugState.name, F.text)
async def process_edit_drug_name(message: types.Message, state: FSMContext):
    drug_name = await valdate_string_from_message(
        message,
        max_length=150,
    )
    if not drug_name:
        return 
    
    state_data = await state.get_data()
    drug_id = state_data['drug_id']
    
    drug = await Drug.objects.aget(id=drug_id)
    protocol_drugs = await Drug.objects.afilter(protocol_id=drug.protocol_id)
    drug.name = drug_name
    
    if not await validate_drugs(message, protocol_drugs, drug):
        return 
   
    await drug.asave()

    await message.answer(
        'Название препарата успешно изменено!',
        reply_markup=reply_doctor_keyboard
    ) 
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(drug.protocol_id)
    )
    await send_edit_protocol_notification_to_patient(
        bot=message.bot,
        protocol_id=drug.protocol_id
    )
    
    await state.clear()
    
    
@router.callback_query(F.data.startswith('edit_first_'))
async def edit_first_take_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    drug_id = callback.data.split('_')[-1]

    await state.update_data(drug_id=drug_id)    
    await callback.message.delete()
    await callback.message.answer(
        'Выберите день первого приёма',
        reply_markup=reply_calendar_keyboard,
    ) 
    await state.set_state(EditDrugState.first_take)
    
    
@router.message(EditDrugState.first_take, F.text)
async def process_edit_first_take(message: types.Message, state: FSMContext):
    first_take = await valdate_first_take_from_message(message)
    if not first_take:
        return 
    
    state_data = await state.get_data()
    drug_id = state_data['drug_id']
    
    drug = await Drug.objects.aget(id=drug_id)
    drug.first_take = first_take
    drug.last_take = first_take + timedelta(days=drug.period)
    await drug.asave()
    
    await message.answer(
        'День первого приёма успешно изменён!',
        reply_markup=reply_doctor_keyboard
    ) 
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(drug.protocol_id)
    )
    await send_edit_protocol_notification_to_patient(
        bot=message.bot,
        protocol_id=drug.protocol_id
    )

    await state.clear()
    
    
@router.callback_query(F.data.startswith('edit_period_'))
async def edit_period_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    drug_id = callback.data.split('_')[-1]

    await state.update_data(drug_id=drug_id)
    await callback.message.delete()
    await callback.message.answer(
        'Отправьте новое количество дней приёма',
        reply_markup=reply_cancel_keyboard,
        parse_mode='HTML',
    ) 
    await state.set_state(EditDrugState.period)
    
    
@router.message(EditDrugState.period, F.text)
async def process_edit_period(message: types.Message, state: FSMContext):
    period = await valdate_period_from_message(message)
    if not period:
        return 
    
    state_data = await state.get_data()
    drug_id = state_data['drug_id']
    
    drug = await Drug.objects.aget(id=drug_id)
    drug.last_take = drug.first_take + timedelta(days=period)
    await drug.asave()
    
    await message.answer(
        'Срок приёма успешно изменён!',
        reply_markup=reply_doctor_keyboard
    )  
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(drug.protocol_id)
    )
    await send_edit_protocol_notification_to_patient(
        bot=message.bot,
        protocol_id=drug.protocol_id
    )
    
    await state.clear()
    
    
@router.callback_query(F.data.startswith('edit_time_'))
async def edit_time_to_take_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    drug_id = callback.data.split('_')[-1]

    await state.update_data(drug_id=drug_id)
    await callback.message.delete()
    await callback.message.answer(
        'Какое новое время приёма препарата?\n\n'
        + default_process_time_to_take_message,
        reply_markup=reply_cancel_keyboard,
        parse_mode='HTML',
    ) 
    await state.set_state(EditDrugState.time_to_take)
    
@router.message(EditDrugState.time_to_take, F.text)
async def process_edit_time_to_take(message: types.Message, state: FSMContext):
    time_to_take = await valdate_time_to_take_from_message(message)
    if not time_to_take:
        return 
    
    state_data = await state.get_data()
    drug_id = state_data['drug_id']
    
    drug = await Drug.objects.aget(id=drug_id)
    protocol_drugs = await Drug.objects.afilter(protocol_id=drug.protocol_id)
    drug.time_to_take = time_to_take
    
    if not await validate_drugs(message, protocol_drugs, drug):
        return 
    
    await drug.asave()
    

    await message.answer(
        'Время приёма препарата успешно изменено!',
        reply_markup=reply_doctor_keyboard
    ) 
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(drug.protocol_id)
    )
    await send_edit_protocol_notification_to_patient(
        bot=message.bot,
        protocol_id=drug.protocol_id
    )
    
    await state.clear()

    

