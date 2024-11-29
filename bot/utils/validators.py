import calendar
from typing import List, Optional, Union
from datetime import datetime, date, time, timedelta

import loguru
from aiogram import types, F, Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asgiref.sync import sync_to_async
from django.utils import timezone

from core import config
from schemas.drug import DrugCreateSchema
from models import Drug


def get_integer_from_string(string: str) -> Optional[int]:
    try:
        integer = int(string)
        return integer
    except ValueError:
        return None
    
    
async def validate_drugs(
    message: types.Message,
    drugs: List[DrugCreateSchema],
    drug_obj: Union[DrugCreateSchema, Drug]
) -> Union[DrugCreateSchema, Drug, None]:
    ununique_drugs = list(
        filter(
            (lambda drug: drug.name == drug_obj.name
            and drug.time_to_take == drug_obj.time_to_take),
            drugs
        )
    )
    
    if ununique_drugs:
        await message.answer(
            'Нельзя добавлять в протокол '
            'несколько препаратов с одинаковым названием '
            'и временем приёма'
        ) 
        return 
    
    return drug_obj
    
    
async def valdate_first_take_from_message(message: types.Message) -> Optional[date]:
    now = timezone.now()
    year = now.year
    month = now.month
    day = get_integer_from_string(message.text)
    
    days_count = calendar.monthrange(year, month)[1]
    
    if not day or day > days_count:
        await message.answer('Выберите число текущего месяца')
        return
    if day < now.day:
        await message.answer('Нельзя выбирать прошедшие числа')
        return
    
    first_take = date(year, month, day)
    
    return first_take
        
        
async def valdate_period_from_message(message: types.Message) -> Optional[int]:
    period = get_integer_from_string(message.text)
    if not period:
        await message.answer('Пожалуйста, введите корректное количество дней приёма')
        return
    if period > 365:
        await message.answer('Длительность приёма не должна превышать 365 дней')
        return
    
    return period
        
        
async def valdate_time_to_take_from_message(
    message: types.Message,
) -> Optional[time]:
    try:
        hour, minute = message.text.split(':')
        time_to_take = time(int(hour), int(minute))
    except ValueError or TypeError:
        await message.answer('Некорректный формат ввода')
        return
    
    return time_to_take


async def valdate_string_from_message(
    message: types.Message,
    min_length: int = 1,
    max_length: int = 150,
) -> Optional[str]:
    string = message.text
    
    if len(string) < min_length:
        await message.answer(
            f'Длина должна более {min_length} символов'
        )
        return
    if len(string) > max_length:
        await message.answer(
            f'Длина не должна превышать {max_length} символов'
        )
        return
        
    return string