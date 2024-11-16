import loguru
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command, CommandObject
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from .fio import DoctorState
from schemas.patient import PatientCreateSchema
from keyboards.reply import get_reply_keyboard
from web.protocols.models import Protocol
from web.patients.models import Patient
from web.doctors.models import Doctor

router = Router()


@router.message(CommandStart())
async def start_command_handler(
    message: types.Message,
    command: CommandObject,
    state: FSMContext,
):
    message_text = (
    f'Привет, {message.from_user.first_name}.'
    )
    
    if command.args is not None:
        protocol_id = command.args
        
        try:
            protocol = await Protocol.objects.get(id=protocol_id)
            patient_create_schema = PatientCreateSchema(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                name=protocol.patient_name,
            )
            patient = await Patient.objects.create(patient_create_schema.model_dump())
            protocol.patient = patient
            await sync_to_async(protocol.save())
        
            await message.answer(
                'Протокол успешно добавлен! Выберите действие.',
                reply_markup=get_reply_keyboard(buttons=('Меню 📁', ))
            )
        except ObjectDoesNotExist:
            await message.answer('Неправильный QR-код')
            return 
    
    
    message_text += '\nОтправь свое ФИО одним сообщением'
    
    try:
        doctor = await Doctor.objects.get(telegram_id=message.from_user.id)
        await message.answer(
            'Вы уже зарегистрированы. Выберите действие.',
            reply_markup=get_reply_keyboard(
                buttons=('Меню 📁', 'Старт нового протокола 📝')
            )
        )
        
    except ObjectDoesNotExist:
        await message.answer(
            message_text, 
            reply_markup=get_reply_keyboard(buttons=('Отмена ❌', ))
    )
        await state.set_state(DoctorState.fio)
        

    
    
    
    
    
        
    
    
    
    
    
    
    
    
    
    

