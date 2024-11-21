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
)
from schemas.doctor import DoctorCreateSchema
from schemas.protocol import ProtocolCreateSchema
from utils.validators import get_integer_from_string
from utils.protocol import get_timedelta_calendar, get_protocol_from_state
from utils.message import default_process_time_to_take_message
from web.doctors.models import Doctor
from web.protocols.models import Protocol
from .state import EditProtocolState

router = Router()


@router.callback_query(F.data.startswith('edit_drugs_'))
async def start_edit_drugs_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    protocol_id = int(callback.data.split('_')[-1])
    await state.update_data(protocol_id=protocol_id)
    await callback.message.delete()
    await callback.message.answer(
        'Отправьте список препаратов одним сообщением через пробел\n\n'
        '<b>Пример:</b> <b><em>Парацетамол Глицин Витамин Д</em></b>',
        reply_markup=reply_cancel_keyboard,
        parse_mode='HTML',
    )    
   
    await state.set_state(EditProtocolState.drugs)
    
    
@router.message(EditProtocolState.drugs, F.text)
async def process_drugs(message: types.Message, state: FSMContext):
    drugs = message.text.split()

    protocol = await get_protocol_from_state(state)
    protocol.drugs = drugs
    await sync_to_async(protocol.save)()

    await message.answer(
        'Cписок препаратов успешно изменён!',
        reply_markup=reply_doctor_keyboard
    ) 
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(protocol.id)
    )
    
    await state.clear()
    
    
@router.callback_query(F.data.startswith('edit_first_take_'))
async def start_edit_first_take_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    protocol_id = int(callback.data.split('_')[-1])
    
    await state.update_data(protocol_id=protocol_id)
    await callback.message.delete()
    await callback.message.answer(
        'Выберите день первого приёма',
        reply_markup=reply_calendar_keyboard,
    ) 
    await state.set_state(EditProtocolState.first_take)
    
    
@router.message(EditProtocolState.first_take, F.text)
async def process_first_take(message: types.Message, state: FSMContext):
    first_take = await valdate_first_take_from_message(message)
    if not first_take:
        return 
    
    protocol = await get_protocol_from_state(state)
    protocol.first_take = first_take
    protocol.last_take = first_take + timedelta(days=protocol.period)
    await sync_to_async(protocol.save)()
    
    await message.answer(
        'День первого приёма успешно изменён!',
        reply_markup=reply_doctor_keyboard
    ) 
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(protocol.id)
    )
    
    await state.clear()
    
    
@router.callback_query(F.data.startswith('edit_period_'))
async def start_edit_period_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    protocol_id = int(callback.data.split('_')[-1])
    
    await state.update_data(protocol_id=protocol_id)
    await callback.message.delete()
    await callback.message.answer(
        'Отправьте новое количество дней приёма',
        reply_markup=reply_cancel_keyboard,
        parse_mode='HTML',
    ) 
    await state.set_state(EditProtocolState.period)
    
    
@router.message(EditProtocolState.period, F.text)
async def process_edit_period(message: types.Message, state: FSMContext):
    period = await valdate_period_from_message(message)
    if not period:
        return 
        
    protocol = await get_protocol_from_state(state)
    protocol.last_take = protocol.first_take + timedelta(days=period)
    await sync_to_async(protocol.save)()
    
    
    await message.answer(
        'Срок приёма успешно изменён!',
        reply_markup=reply_doctor_keyboard
    )  
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(protocol.id)
    )
    
    await state.clear()
    
    
@router.callback_query(F.data.startswith('edit_time_to_take_'))
async def start_edit_time_to_take_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    protocol_id = int(callback.data.split('_')[-1])
    
    await state.update_data(protocol_id=protocol_id)
    await callback.message.delete()
    await callback.message.answer(
        'Какое новое время приёма препаратов?\n\n'
        + default_process_time_to_take_message,
        reply_markup=reply_cancel_keyboard,
        parse_mode='HTML',
    ) 
    await state.set_state(EditProtocolState.time_to_take)
    
@router.message(EditProtocolState.time_to_take, F.text)
async def process_edit_time_to_take(message: types.Message, state: FSMContext):
    time_to_take = await valdate_time_to_take_from_message(message)
    if not time_to_take:
        return 
        
    protocol = await get_protocol_from_state(state)
    protocol.time_to_take = time_to_take
    await sync_to_async(protocol.save)()
    

    await message.answer(
        'Время приёма препаратов успешно изменено!',
        reply_markup=reply_doctor_keyboard
    ) 
    await message.answer(
        'Посмотреть протокол',
        reply_markup=get_protocol_inline_button_keyboard(protocol.id)
    )
    
    await state.clear()

    

