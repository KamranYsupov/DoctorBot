import loguru
from aiogram import types, F, Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asgiref.sync import sync_to_async

from keyboards.inline import get_inline_keyboard
from keyboards.reply import reply_keyboard_remove, get_reply_keyboard
from schemas.doctor import DoctorCreateSchema
from web.doctors.models import Doctor

router = Router()


class DoctorState(StatesGroup):
    fio = State()


@router.message(
    StateFilter('*'),
    or_f(Command('cancel'), (F.text.lower() == 'отмена ❌'))
)
async def cancel_handler(
        message: types.Message,
        state: FSMContext,
):
    await message.answer(
        'Действие отменено',
        reply_markup=reply_keyboard_remove,
    )
    await state.clear()


@router.message(DoctorState.fio, F.text)
async def process_fio(message: types.Message, state: FSMContext):
    fio = message.text
    if len(fio) > 150:
        return await message.answer('Длина не должна превышать 150 символов')
    
    doctor_create_schema = DoctorCreateSchema(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        fio=fio
    )
    await Doctor.objects.acreate(**doctor_create_schema.model_dump())
    await message.answer(
        'Регистрация прошла успешно! Выберите действие.',
        reply_markup=get_reply_keyboard(
            buttons=('Меню 📁', 'Старт нового протокола 📝')
        )
    )
    
    await state.clear()
    