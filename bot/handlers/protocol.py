import calendar
from datetime import datetime, date, time, timedelta

import loguru
from aiogram import types, F, Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.conf import settings

from core import config
from keyboards.inline import get_inline_keyboard
from keyboards.reply import (
    reply_keyboard_remove, 
    get_reply_keyboard,
    reply_cancel_keyboard,
    reply_calendar_keyboard,
)
from schemas.doctor import DoctorCreateSchema
from schemas.protocol import ProtocolCreateSchema
from utils.validators import (
    valdate_string_from_message,
    valdate_first_take_from_message,
    valdate_period_from_message,
    valdate_time_to_take_from_message,
)
from utils.protocol import get_timedelta_calendar
from utils.message import default_process_time_to_take_message
from web.doctors.models import Doctor
from web.protocols.models import Protocol
from .state import CreateProtocolState

router = Router()
    
    
@router.message(F.text.casefold() == 'старт нового протокола 📝')
async def start_protocol_handler(message: types.Message, state: FSMContext):
    await message.answer('Введите имя пациента', reply_markup=reply_cancel_keyboard)    
    await state.set_state(CreateProtocolState.patient_name)
    
    
@router.message(CreateProtocolState.patient_name, F.text)
async def process_patient_name(message: types.Message, state: FSMContext):
    patient_name = await valdate_string_from_message(
        message,
        max_length=150,
    )
    if not patient_name:
        return 
    
    await state.update_data(patient_name=patient_name)
    await message.answer('Введите название препарата') 
    await state.set_state(CreateProtocolState.drugs)
    
    

@router.message(CreateProtocolState.drugs, F.text)
async def process_drug_name(message: types.Message, state: FSMContext):
    drug_name = await valdate_string_from_message(
        message,
        max_length=150,
    )
    if not drug_name:
        return 
    
    state_data = await state.get_data()
    drugs = state_data.get('drugs')
    if not drugs:
        drugs = []
        
    drugs.append(drug_name) 
    await state.update_data(drugs=drugs)
    
    if len(drugs) > 1:
        return await send_finish_protocol_message(
            message,
            text=f'Препарат <b>{drug_name}</b> добавлен!\nВыберите действие',
        )
        
    await message.answer(
        'Выберите день первого приёма',
        reply_markup=reply_calendar_keyboard,
    ) 
    await state.set_state(CreateProtocolState.first_take)
    

@router.message(CreateProtocolState.first_take, F.text)
async def process_first_take(message: types.Message, state: FSMContext):
    first_take = await valdate_first_take_from_message(message)
    if not first_take:
        return 
    
    await state.update_data(first_take=first_take)
    await message.answer(
        'Сколько дней нужно принемать лекарства?',
        reply_markup=reply_cancel_keyboard
    ) 
    await state.set_state(CreateProtocolState.period)
    
    
@router.message(CreateProtocolState.period, F.text)
async def process_period(message: types.Message, state: FSMContext):
    period = await valdate_period_from_message(message)
    if not period:
        return 
    
    await state.update_data(period=period)
    await message.answer(
        'В какое время нужно принемать препараты?\n\n'\
         + default_process_time_to_take_message,
        parse_mode='HTML',
    ) 
    await state.set_state(CreateProtocolState.time_to_take)
    
    

@router.message(CreateProtocolState.time_to_take, F.text)
async def process_time_to_take(message: types.Message, state: FSMContext):
    time_to_take = await valdate_time_to_take_from_message(message) 
    if not time_to_take:
        return 
    
    await state.update_data(time_to_take=time_to_take)
    await send_finish_protocol_message(message)
    
    
@router.callback_query(F.data == 'create_protocol')
async def create_protocol_handler(callback: types.CallbackQuery, state: FSMContext):
    protocol_data = await state.get_data()
    doctor = await Doctor.objects.aget(telegram_id=callback.from_user.id)
    protocol_data['doctor_id'] = doctor.id
    
    first_take = protocol_data['first_take']
    period = protocol_data['period']
    
    timedelta_calendar = get_timedelta_calendar(first_take, period)
    protocol_data['reception_calendar'] = timedelta_calendar
    protocol_data['notifications_calendar'] = timedelta_calendar
    protocol_data['last_take'] = first_take + timedelta(days=period)
    
    protocol_create_schema = ProtocolCreateSchema(**protocol_data)
    protocol = await Protocol.objects.acreate(**protocol_create_schema.model_dump())
    protocol_start_link = f'{config.BOT_LINK}?start={protocol.id}'
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=f'{config.QR_CODE_API_GENERATOR_URL}{protocol_start_link}',
        caption='Протокол создан! <b>QR-код</b>:\n'
        f'Ссылка для пациента: {protocol_start_link}',
        parse_mode='HTML',
        reply_markup=get_reply_keyboard(
            buttons=('Меню 📁', 'Старт нового протокола 📝')
        )
    )
    await state.clear()
    
    
@router.callback_query(F.data == 'add_drug')
async def add_drug_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('Введите название препарата') 
    await state.set_state(CreateProtocolState.drugs)
    
    
async def send_finish_protocol_message(
    message: types.Message,
    text: str = 'Выберите действие',
    parse_mode: str = 'HTML'
):
    await message.answer(
        text,
        reply_markup=get_inline_keyboard(
            buttons={
                'Создать протокол 🧾': 'create_protocol',
                'Добавить препарат 💊': 'add_drug',
            }
        ),
        parse_mode=parse_mode
    )
   
    
@router.callback_query(F.data.startswith('complete_protocol_'))
async def complete_protocol(callback: types.CallbackQuery):
    protocol_id = int(callback.data.split('_')[-1])
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    protocol = await Protocol.objects.aget(id=protocol_id)
    drugs_taken = protocol.reception_calendar.get(current_date_strformat)
    
    time_to_take = timezone.make_aware(
        timezone.datetime.combine(
            now.date(),
            protocol.time_to_take
        )
    )
        
    if now > time_to_take + timedelta(
        minutes=settings.PROTOCOL_DRUGS_TAKE_INTERVAL
    ) and not drugs_taken:
        await callback.message.edit_text('Вы пропустили приём.')
        return 
    
    if not drugs_taken:
        protocol.reception_calendar.update({current_date_strformat: True})
        await sync_to_async(protocol.save)()
    
        await callback.message.edit_text('Приём выполнен ✅')
        return 
       
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
   
 
    
    
    
    
