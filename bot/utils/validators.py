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


def get_integer_from_string(string: str) -> int | None:
    try:
        integer = int(string)
        return integer
    except ValueError:
        return None
    
    
async def valdate_first_take_from_message(message: types.Message) -> date | None:
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
        
        
async def valdate_period_from_message(message: types.Message) -> int | None:
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
    first_take: date,
) -> time | None:
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
) -> str | None:
    string = message.text
    
    if len(string) < min_length:
        return await message.answer(
            f'Длина должна более {min_length} символов'
        )
    if len(string) > max_length:
        return await message.answer(
            f'Длина не должна превышать {max_length} символов'
        )
        
    return string