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
from keyboards.inline import get_inline_keyboard
from keyboards.reply import (
    reply_keyboard_remove, 
    get_reply_keyboard,
    reply_cancel_keyboard,
    reply_calendar_keyboard,
)
from schemas.doctor import DoctorCreateSchema
from schemas.protocol import ProtocolCreateSchema
from utils.validators import get_integer_from_string
from utils.protocol import get_timedelta_calendar
from web.doctors.models import Doctor
from web.protocols.models import Protocol

router = Router()


class ProtocolState(StatesGroup):
    patient_name = State()
    drugs = State()
    first_take = State()
    period = State()
    time_to_take = State()
    
    
@router.message(F.text.casefold() == 'старт нового протокола 📝')
async def start_protocol_handler(message: types.Message, state: FSMContext):
    await message.answer('Введите имя пациента', reply_markup=reply_cancel_keyboard)    
    await state.set_state(ProtocolState.patient_name)
    
    
@router.message(ProtocolState.patient_name, F.text)
async def process_patient_name(message: types.Message, state: FSMContext):
    patient_name = message.text
    if len(patient_name) > 150:
        return await message.answer(
            'Длина имени не должна превышать 150 символов'
        )
    
    await state.update_data(patient_name=patient_name)
    await message.answer('Введите название препарата') 
    await state.set_state(ProtocolState.drugs)
    
    

@router.message(ProtocolState.drugs, F.text)
async def process_drug_name(message: types.Message, state: FSMContext):
    drug_name = message.text
    if len(drug_name) > 150:
        return await message.answer(
            'Длина названия препарата не должна превышать 150 символов'
        )
    
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
    await state.set_state(ProtocolState.first_take)
    

@router.message(ProtocolState.first_take, F.text)
async def process_first_take(message: types.Message, state: FSMContext):
    now = timezone.now()
    year = now.year
    month = now.month
    day = get_integer_from_string(message.text)
    
    days_count = calendar.monthrange(year, month)[1]
    
    if not day or day > days_count:
        return await message.answer('Выберите число текущего месяца')
    if day < now.day:
        return await message.answer('Нельзя выбирать прошедшие числа')
    #if day == now.day:
    #    return await message.answer('Нельзя выбирать текущую дату')
    
    first_take = date(year, month, day)
    
    await state.update_data(first_take=first_take)
    await message.answer(
        'Сколько дней нужно принемать лекарства?',
        reply_markup=reply_cancel_keyboard
    ) 
    await state.set_state(ProtocolState.period)
    
    
@router.message(ProtocolState.period, F.text)
async def process_period(message: types.Message, state: FSMContext):
    period = get_integer_from_string(message.text)
    if not period:
        await message.answer('Пожалуйста, введите корректное количество дней приёма')
        return
    if period > 365:
        await message.answer('Длительность приёма не должна превышать 365 дней')
        return
    
    await state.update_data(period=period)
    await message.answer(
        'В какое время нужно принемать лекарства?\n\n'
        'Отправь сообщение в формате <em><b>{час}:{минута}</b></em>.\n'
        '<b>Пример:</b> <b><em>12:35</em></b>',
        parse_mode='HTML',
    ) 
    await state.set_state(ProtocolState.time_to_take)
    
    

@router.message(ProtocolState.time_to_take, F.text)
async def process_time_to_take(message: types.Message, state: FSMContext):
    try:
        hour, minute = message.text.split(':')
        time_to_take = (time(int(hour), int(minute)))
    except ValueError or TypeError:
        await message.answer('Некорректный формат ввода')
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
    protocol_data['notificatons_calendar'] = timedelta_calendar
    protocol_data['last_take'] = first_take + timedelta(days=period)
    
    protocol_create_schema = ProtocolCreateSchema(**protocol_data)
    protocol = await Protocol.objects.acreate(**protocol_create_schema.model_dump())
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=f'{config.QR_CODE_API_GENERATOR_URL}{config.BOT_LINK}?start={protocol.id}',
        caption='Протокол создан! <b>QR-код</b>:',
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
    await state.set_state(ProtocolState.drugs)
    
    
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
    current_date = now.date()
    
    protocol = await Protocol.objects.aget(id=protocol_id)
    protocol.reception_calendar.update({current_date.strftime('%d.%m.%Y'): True})
    await sync_to_async(protocol.save)()
    
    await callback.message.edit_text('Прием выполнен ✅')
    
    
