import uuid
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
from orm.protocol import get_patient_names_and_ulids_by_doctor_id
from utils.pagination import Paginator, get_pagination_buttons
from utils.message import (
    get_protocol_info_message,
    get_drug_info_message,
)
from models import Patient, Drug, Doctor, Protocol

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
    

@router.callback_query(F.data == 'faq')
async def faq_callback_handler(callback: types.CallbackQuery):
    with open('FAQ.txt', 'r', encoding='utf-8') as file:
        message_text = file.read()
        
    await callback.message.edit_text(
        text=message_text,
        reply_markup=get_inline_keyboard(
            buttons={'Назад 🔙': 'menu'}, 
        ),
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
        patient_names_and_ulids = \
            await get_patient_names_and_ulids_by_doctor_id(
            doctor_id=telegram_user.id
        )
        paginator_data['array'] = patient_names_and_ulids
        paginator = Paginator(**paginator_data)
        
        for patient_name, patient_ulid in paginator.get_page():
            buttons[patient_name] = f'doc_p_{patient_ulid}_1'
                
    elif isinstance(telegram_user, Patient):
        message_text += 'Выберите врача'
        doctors = await get_patient_doctors(patient_id=telegram_user.id)
        
        paginator_data['array'] = doctors
        paginator = Paginator(**paginator_data)
        
        for doctor in paginator.get_page():
            buttons[f'Врач: {doctor.fio}'] = f'pat_p_{doctor.id}_1'

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
    
    
@router.callback_query(F.data.startswith('doc_p_'))
async def doctor_protocols_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    patient_ulid = callback_data[-2]
    page_number = int(callback_data[-1])
    message_text = 'Выберите протокол'
    buttons = {}
    
    protocols = await Protocol.objects.afilter(
        patient_ulid=patient_ulid,
        doctor__telegram_id=callback.from_user.id
    )
    paginator = Paginator(
        array=protocols,
        page_number=page_number,
        per_page=3,
    )
    
    page = paginator.get_page()
    for protocol in page:
        buttons[f'{protocol.patient_name} | ID: {protocol.id}' ] = \
            f'prcl_{protocol.id}_{page_number}'
        
    sizes = (1, ) * len(page)
    pagination_buttons = get_pagination_buttons(
        paginator,
        prefix=f'doc_p_{protocol.patient_ulid}'
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
    
    
@router.callback_query(F.data.startswith('pat_p_'))
async def patient_protocols_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    doctor_id = callback_data[-2]
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
        per_page=1,
    )
    for protocol in paginator.get_page():
        message_text += await get_protocol_info_message(protocol) + '\n\n'
        
    sizes = (2, 1)
    buttons.update(
        get_pagination_buttons(paginator, prefix=f'pat_p_{doctor_id}')
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


@router.callback_query(F.data.startswith('prcl_'))
async def protocol_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    protocol_id = callback_data[-2]
    page_number = callback_data[-1]
    reply_markup = None
    
    protocol = await Protocol.objects.aget(id=protocol_id)
    telegram_user = await get_doctor_or_patient(callback.from_user.id)
    add_link = False 
    
    if isinstance(telegram_user, Doctor):
        reply_markup = get_inline_keyboard(
            buttons={
                'Редактировать 📝': f'edit_p_{protocol.id}_{page_number}',
                'Удалить 🗑': f'pre_rm_{protocol.id}_{page_number}',
                'Назад 🔙': f'doc_p_{protocol.patient_ulid}_{page_number}'
            },
            sizes=(1, 1, 1) 
        )
        add_link = True
    
    message_text = await get_protocol_info_message(
        protocol,
        add_link=add_link,
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    
@router.callback_query(F.data.startswith('pre_rm_'))
async def pre_remove_protocol_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    protocol_id = callback_data[-2]
    page_number = callback_data[-1]
    
    await callback.message.edit_text(
        '<b>Вы уверены?</b>',
        reply_markup=get_inline_keyboard(
            buttons={
                'Да': f'rm_p_{protocol_id}_{page_number}',
                'Нет': f'prcl_{protocol_id}_{page_number}'
            },
            sizes=(2, 1)
        ),
        parse_mode='HTML'
    )
    
    
@router.callback_query(F.data.startswith('rm_p_'))
async def remove_protocol_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    protocol_id = callback_data[-2]
    page_number = callback_data[-1]
    
    protocol = await Protocol.objects.aget(id=protocol_id)
    await sync_to_async(protocol.delete)()
    
    await callback.message.edit_text(
        '<b>Протокол успешно удалён ✅</b>',
        reply_markup=get_inline_keyboard(
            buttons={'Назад 🔙': f'protocols_{page_number}'}
        ),
        parse_mode='HTML'
    )
    
    
@router.callback_query(F.data.startswith('edit_p_'))
async def edit_protocol_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    protocol_id = callback_data[-2]
    page_number = int(callback_data[-1])
    buttons = {}
    message_text = 'Выберите препарат' 
    
    protocol = await Protocol.objects.aget(id=protocol_id)  
    drugs = await sync_to_async(protocol.drugs.all)()
    
    async for drug in drugs:
        button_str = f'{drug.name} | {drug.time_to_take.strftime("%H:%M")}' 
        buttons[button_str] = f'edit_drug_{drug.id}_{page_number}'
        
    buttons.update({'Назад 🔙': f'prcl_{drug.protocol_id}_{page_number}'})
    sizes = (1, ) * len(buttons)    
      
    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes,        
        ),
        parse_mode='HTML'
    )
    
    
@router.callback_query(F.data.startswith('edit_drug_'))
async def edit_drug_callback_handler(callback: types.CallbackQuery):
    callback_data = callback.data.split('_')
    drug_id = callback_data[-2]
    page_number = int(callback_data[-1])

    message_text = '<b>Редактирование 📝</b>\n\n'
    
    drug = await Drug.objects.aget(id=drug_id)
    message_text += get_drug_info_message(drug)
    buttons = {
        'Изменить название 📝': f'edit_drugs_{drug.id}',
        'Изменить дату первого приёма 📆': f'edit_first_{drug.id}',
        'Изменить срок приёма ⏳': f'edit_period_{drug.id}',
        'Изменить время приёма ⏰': f'edit_time_{drug.id}',
        'Назад 🔙': f'edit_p_{drug.protocol_id}_{page_number}' 
    }
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=(1, 1, 1, 1, 1),        
        ),
        parse_mode='HTML'
    )
    
    