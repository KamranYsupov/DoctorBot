import calendar
from datetime import datetime, date, time

import loguru
from aiogram import types, F, Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asgiref.sync import sync_to_async

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
from web.doctors.models import Doctor
from web.protocols.models import Protocol

router = Router()
    
    
@router.message(F.text.casefold() == 'меню 📁')
async def menu_handler(message: types.Message, state: FSMContext):
    await message.answer('Меню 📁', reply_markup=reply_cancel_keyb