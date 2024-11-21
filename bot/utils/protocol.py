from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram import Bot

from web.protocols.models import Protocol
from keyboards.inline import get_inline_keyboard
from web.doctors.models import Doctor
from web.patients.models import Patient


def get_timedelta_calendar(first_take: datetime, period: int) -> dict:    
    timedelta_calendar = {}
    
    for day in range(period+1):
        take = first_take + timedelta(days=day)
        timedelta_calendar[take.strftime('%d.%m.%Y')] = False
        
    return timedelta_calendar


async def get_protocol_from_state(state: FSMContext) -> Protocol:
    state_data = await state.get_data()
    protocol_id = int(state_data.get('protocol_id'))
    
    return await Protocol.objects.aget(id=protocol_id)


async def send_edit_protocol_notification_to_patient(
    bot: Bot,
    protocol: Protocol,
) -> None:
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
            buttons={'Посмотреть изменения 🔎': f'protocol_1_{protocol.id}'}
        )
    )