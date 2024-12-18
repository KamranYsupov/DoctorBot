from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram import Bot

from keyboards.inline import get_inline_keyboard
from models import Patient, Doctor, Protocol    


async def send_edit_protocol_notification_to_patient(
    bot: Bot,
    protocol_id: int,
) -> None:
    protocol = await Protocol.objects.aget(id=protocol_id)
    patient_list = await Patient.objects.afilter(id=protocol.patient_id)
    if not patient_list:
        return
    
    try:
        patient = patient_list[0]
    except IndexError:
        return 
    
    doctor = await Doctor.objects.aget(id=protocol.doctor_id)
    await bot.send_message(
        chat_id=patient.telegram_id,
        text=f'Врач {doctor.fio} изменил ваш протокол.',
        reply_markup=get_inline_keyboard(
            buttons={'Посмотреть изменения 🔎': f'prcl_{protocol.id}_1'}
        )
    )