import calendar
from datetime import datetime, timedelta, date, time

import loguru
from aiogram import types, F, Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from asgiref.sync import sync_to_async

from core import config
from keyboards.inline import get_inline_keyboard
from keyboards.reply import (
    reply_keyboard_remove, 
    get_reply_keyboard,
    reply_cancel_keyboard,
    reply_menu_keyboard,
)
from schemas.doctor import DoctorCreateSchema
from schemas.protocol import ProtocolCreateSchema
from orm.telegram_user import get_doctor_or_patient
from utils.pagination import Paginator, get_pagination_buttons
from utils.message import get_protocol_info_message
from web.patients.models import Patient
from web.doctors.models import Doctor
from web.protocols.models import Protocol

router = Router()
    
    
@router.message(F.text.casefold() == 'меню 📁')
async def menu_handler(message: types.Message):
    await message.answer('Меню 📁', reply_markup=reply_menu_keyboard)
    

@router.message(F.text.casefold() == 'протоколы 🗂️')
async def protocols_message_handler(message: types.Message):
    await protocols_handler(
        message,
        from_user_id=message.from_user.id,
    )
    
    
@router.callback_query(F.data.startswith('protocols_'))
async def protocols_callback_handler(callback: types.CallbackQuery):
    page_number = int(callback.data.split('_')[-1])
    await protocols_handler(
        callback.message,
        from_user_id=callback.from_user.id,
        page_number=page_number
    )
    
    
@router.callback_query(F.data.startswith('doctor_protocols_'))
async def doctor_protocols_callback_handler(callback: types.CallbackQuery):
    message_text = ''
    callback_data = callback.data.split('_')
    buttons = {}
    doctor_id = int(callback_data[-2])
    page_number = int(callback_data[-1])
    
    protocols = await Protocol.objects.afilter(doctor_id=doctor_id)
    paginator = Paginator(
        array=protocols,
        page_number=page_number,
        per_page=3,
    )
    for protocol in paginator.get_page():
        message_text += get_protocol_info_message(protocol)
        
    sizes = (2, 1)
    buttons.update(
        get_pagination_buttons(paginator, prefix=f'doctor_protocols_{doctor_id}')
    )
    
    if len(buttons.items()) == 1:
        sizes = (1, 1)
        
    buttons['Назад 🔙'] = f'protocols_1'
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes      
        ),
        parse_mode='HTML'
    )

@router.callback_query(F.data.startswith('protocol_'))
async def protocol_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    protocol_id = callback_data[-1]
    page_number = int(callback_data[-2])
    
    protocol = await Protocol.objects.aget(id=protocol_id)
    message_text = get_protocol_info_message(protocol)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons={
                'Редактировать 📝': f'edit_protocol_{page_number}_{protocol.id}',
                'Назад 🔙': f'protocols_{page_number}'
            }        
        ),
        parse_mode='HTML'
    )
    

@router.callback_query(F.data.startswith('edit_protocol_'))
async def protocol_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    protocol_id = int(callback.data.split('_')[-1])
    page_number = int(callback_data[-2])
     
    message_text = '<b>Редактирование 📝</b>\n\n'
    
    protocol = await Protocol.objects.aget(id=protocol_id)
    message_text += get_protocol_info_message(protocol)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons={
                'Изменить препараты 📝': f'edit_drugs_{protocol.id}',
                'Изменить дату первого приема 📝': f'edit_first_take_{protocol.id}',
                'Изменить срок приема 📝': f'edit_period_{protocol.id}',
                'Изменить время приема 📝': f'edit_time_to_take_{protocol.id}',
                'Назад 🔙': f'protocol_{page_number}_{protocol_id}'
            }        
        ),
        parse_mode='HTML'
    )
    
    
    
    
async def protocols_handler(
    message: types.Message,
    from_user_id: int,
    page_number: int = 1,
    per_page: int = 5,
) -> None:
    message_text = '<b>Протоколы</b>\n\n'
    button_prefix = ''
    buttons = {}
    
    telegram_user = await get_doctor_or_patient(telegram_id=from_user_id)
  
    protocols_query_data = {'select_relations': ('doctor', 'patient')}        
    
    if isinstance(telegram_user, Doctor):
        message_text += 'Выберите пациента'
        protocols_query_data['doctor_id'] = telegram_user.id
    elif isinstance(telegram_user, Patient):
        message_text += 'Выберите врача'
        protocols_query_data['patient_id'] = telegram_user.id
    else:
        return
        
    protocols = await Protocol.objects.afilter(**protocols_query_data)
    paginator = Paginator(
        array=protocols,
        page_number=page_number,
        per_page=per_page,
    )
    for protocol in paginator.get_page():
        if isinstance(telegram_user, Doctor):
            buttons[protocol.patient_name] = f'protocol_{page_number}_{protocol.id}'
        else:
            buttons[f'Врач: {protocol.doctor.fio}'] = \
                f'doctor_protocols_{protocol.doctor.id}_{page_number}'
        
    buttons.update(get_pagination_buttons(paginator, prefix='protocols'))
    
    message_data = dict(
        text=message_text, 
        reply_markup=get_inline_keyboard(
            buttons=buttons, 
            sizes=(1, 1, 1, 1, 1, 2)
        ),
        parse_mode='HTML',
    )
    
    try:
        await message.edit_text(**message_data)
    except TelegramBadRequest:
        await message.answer(**message_data)