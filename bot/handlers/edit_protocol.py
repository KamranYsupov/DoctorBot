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
from .state import EditProtocolState

router = Router()


@router.callback_query(F.data.startswith.startswith('edit_drugs_'))
async def start_edit_drugs_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    protocol_id = int(callback.data.split('_')[-1])
    await state.update_data(protocol_id=protocol_id)
    await message.edit_text(
        'Введите отправте список препаратов одним сообщением через пробел\n\n'
        '<b>Пример:</b> <b><em>Парацетамол Глицин Витамин Д</em></b>',
        reply_markup=reply_cancel_keyboard
    )    
    await state.set_state(EditProtocolState.drugs)
    
    
@router.message(EditProtocolState.drugs, F.text)
async def process_drugs(message: types.Message, state: FSMContext):
    drugs = message.text.split()
    await state.update_data(drugs=drugs)
    
    state_data = await state.get_data()
    protocol = await Protocol.objects.afilter(id=state_data.get('protocol_id'))
    protocol.drugs = state_data['drugs']
    await sync_to_async(protocol.save)()
    
    await message.answer('Cписок препаратов успешно изменен') 
    await state.clear()
   