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
from keyboards.inline import get_inline_keyboard, get_menu_keyboard
from keyboards.reply import (
    reply_keyboard_remove, 
    get_reply_keyboard,
    reply_cancel_keyboard,
    reply_menu_keyboard,
)
from schemas.doctor import DoctorCreateSchema
from schemas.protocol import ProtocolCreateSchema
from orm.telegram_user import get_doctor_or_patient
from orm.patient import get_patient_doctors 
from orm.protocol import get_patients_names_by_doctor_id
from utils.pagination import Paginator, get_pagination_buttons
from utils.message import get_protocol_info_message
from web.patients.models import Patient
from web.doctors.models import Doctor
from web.protocols.models import Protocol

router = Router()
    
    
@router.message(F.text.casefold() == 'меню 📁')
async def menu_handler(message: types.Message):
    await message.answer(
        'Меню 📁',
        reply_markup=get_menu_keyboard()
    )
    

@router.callback_query(F.data == 'menu')
async def menu_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        'Меню 📁',
        reply_markup=get_menu_keyboard()
    )
    
    
async def protocols_menu_handler(
    message: types.Message,
    from_user_id: int,
    page_number: int = 1,
    per_page: int = 3,
) -> None:
    message_text = '<b>Протоколы</b>\n\n'
    buttons = {}
    objects_list = []
    
    telegram_user = await get_doctor_or_patient(telegram_id=from_user_id)
  
    paginator_data = {
        'page_number': page_number,
        'per_page': per_page,
    }
        
    if isinstance(telegram_user, Doctor):
        message_text += 'Выберите пациента'
        patients_names = await get_patients_names_by_doctor_id(
            doctor_id=telegram_user.id
        )
        paginator_data['array'] = patients_names
        paginator = Paginator(**paginator_data)
        
        for patient_name in paginator.get_page():
            buttons[patient_name] = f'doctor_protocols_{patient_name}_1'
                
    elif isinstance(telegram_user, Patient):
        message_text += 'Выберите врача'
        doctors = await get_patient_doctors(patient_id=telegram_user.id)
        
        paginator_data['array'] = doctors
        paginator = Paginator(**paginator_data)
        
        for doctor in paginator.get_page():
            buttons[f'Врач: {doctor.fio}'] = f'patient_protocols_{doctor.id}_1'

    else:
        return
            
    sizes = (1, ) * len(paginator.get_page())
    pagination_buttons = get_pagination_buttons(paginator, prefix='protocols')
    if len(pagination_buttons.items()) == 1:
        sizes += (1, 1)
    else:
        sizes += (2, 1)
        
    buttons.update(pagination_buttons)
    buttons['Назад 🔙'] = f'menu'
    
    message_data = dict(
        text=message_text, 
        reply_markup=get_inline_keyboard(
            buttons=buttons, 
            sizes=sizes
        ),
        parse_mode='HTML',
    )
    
    try:
        await message.edit_text(**message_data)
    except TelegramBadRequest:
        await message.answer(**message_data)
        
        
@router.callback_query(F.data.startswith('protocols_'))
async def protocols_callback_handler(callback: types.CallbackQuery):
    page_number = int(callback.data.split('_')[-1])
    await protocols_menu_handler(
        callback.message,
        from_user_id=callback.from_user.id,
        page_number=page_number
    )
    
    
@router.callback_query(F.data.startswith('doctor_protocols_'))
async def doctor_protocols_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    patient_name = callback_data[-2]
    page_number = int(callback_data[-1])
    message_text = 'Выберите протокол'
    buttons = {}
    
    protocols = await Protocol.objects.afilter(
        patient_name=patient_name,
        doctor__telegram_id=callback.from_user.id
    )
    paginator = Paginator(
        array=protocols,
        page_number=page_number,
        per_page=3,
    )
    
    page = paginator.get_page()
    for protocol in page:
        buttons[f'ID: {protocol.id} | {protocol.patient_name}' ] = \
            f'protocol_{page_number}_{protocol.id}'
        
    sizes = (1, ) * len(page)
    pagination_buttons = get_pagination_buttons(
        paginator,
        prefix=f'doctor_protocols_{patient_name}'
    )
    
    if len(pagination_buttons.items()) == 1:
        sizes += (1, 1)
    else:
        sizes += (2, 1)
        
    buttons.update(pagination_buttons)
    buttons['Назад 🔙'] = f'protocols_1'
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes      
        ),
        parse_mode='HTML'
    )
    
    
@router.callback_query(F.data.startswith('patient_protocols_'))
async def patient_protocols_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    doctor_id = int(callback_data[-2])
    page_number = int(callback_data[-1])
    message_text = ''
    buttons = {}
    
    protocols = await Protocol.objects.afilter(
        doctor_id=doctor_id,
        patient__telegram_id=callback.from_user.id
    )
    paginator = Paginator(
        array=protocols,
        page_number=page_number,
        per_page=3,
    )
    for protocol in paginator.get_page():
        message_text += get_protocol_info_message(protocol) + '\n\n'
        
    sizes = (2, 1)
    buttons.update(
        get_pagination_buttons(paginator, prefix=f'patient_protocols_{doctor_id}')
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
    protocol_id = int(callback_data[-1])
    page_number = int(callback_data[-2])
    
    protocol = await Protocol.objects.aget(id=protocol_id)
    message_text = get_protocol_info_message(protocol)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons={
                'Редактировать 📝': f'edit_protocol_{protocol.id}_{page_number}',
                'Назад 🔙': f'doctor_protocols_{protocol.patient_name}_{page_number}'
            }        
        ),
        parse_mode='HTML'
    )
    

@router.callback_query(F.data.startswith('edit_protocol_'))
async def protocol_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    protocol_id = int(callback_data[-2])
    page_number = int(callback_data[-1])
     
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
        sizes=(1, 1, 1, 1, 1)
        parse_mode='HTML'
    )
    