import asyncio
from datetime import timedelta, date, datetime

import loguru
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from asgiref.sync import sync_to_async

from .models import Drug
from .service import get_unnotificated_drugs
from web.services.telegram_service import telegram_service
from web.services.smsc_service import smsc_service 
from web.utils.requests import send_request_until_success


@shared_task(ignore_result=True)
def send_reminder_before_time_to_take(
    drug_id: str, 
    minutes_before: int,
    add_complete_take_button: bool = False
):
    """
    Задача для уведомления пациента
    о скором приёме препарата
    """
    drug = Drug.objects.get(id=drug_id)
    reply_markup = None
    
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    if drug.reception_calendar.get(current_date_strformat):
        return 
    
    telegram_id = drug.protocol.patient.telegram_id
    
    text = ''
    if minutes_before == 1:
        text += (
	    f'Осталась <b>{minutes_before} минута</b>\n\n' 
	    'Обязательно нажмите кнопку <em><b>«Выполнено ✅»</b></em>, '
	    'чтобы подтвердить прием лекарства'
	)
    else:
        text += f'Осталось <b>{minutes_before} минут</b>'
        
    text += f' до приёма <b><em>{drug.name}</em></b>'
    
    if add_complete_take_button:
        inline_keyboard = [[
            {
                'text': 'Выполнено ✅',
                'callback_data': f'complete_drug_{drug_id}'
            }
        ]]
    
        reply_markup = {'inline_keyboard': inline_keyboard}

    response = send_request_until_success(
        telegram_service.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=reply_markup,
        )
    )
    
    return response.status_code
    
    
@shared_task(ignore_result=True)
def call_patient_before_time_to_take(drug_id: str):
    """
    Задача для создания телефоного вызова 
    с напоминанием о скором приёме препарата
    """
    
    drug = Drug.objects.get(id=drug_id)    
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')

    if drug.reception_calendar.get(current_date_strformat):
        return 
    
    patient = drug.protocol.patient
    doctor = drug.protocol.doctor
    call_message = (
        settings.CALL_PAITIENT_BEFORE_TIME_TO_TAKE_MESSAGE.format(
            patient=patient.name,
            doctor=doctor.fio
        )
    )
    
    response = send_request_until_success(
        smsc_service.create_call(
            phone=patient.phone_number,
            message=call_message, 
        )
    )
    
    return response.status_code


@shared_task(ignore_result=True)
def send_reminder_after_time_to_take(drug_id: str):
    """
    Задача для уведомления пациента
    о приёме препарата после времени приёма
    """
    
    drug = Drug.objects.get(id=drug_id)
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    if drug.reception_calendar.get(current_date_strformat):
        return 
    
    telegram_id = drug.protocol.patient.telegram_id
    
    text = (
        f'Напоминаем, что пора принять <b><em>{drug.name}</em></b>'
    )
        
    response = send_request_until_success(
        telegram_service.send_message(
            chat_id=telegram_id,
            text=text,
        )
    )
    
    return response.status_code
    

@shared_task(ignore_result=True)
def notify_doctor_about_drug_take_miss(drug_id: str):
    """
    Задача для уведомления доктора 
    о пропуске приёма препарата пациентом
    """
    
    drug = Drug.objects.get(id=drug_id)
    protocol = drug.protocol
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    datetime_to_take = timezone.make_aware(
        timezone.datetime.combine(
            now.date(),
            drug.time_to_take
        )
    )

    if drug.reception_calendar.get(current_date_strformat):
        return 

    text = (
        f'Пациент {protocol.patient_name} '
        f'пропустил приём <b><em>{drug.name}</em></b> по протоколу ' 
        f'<b>ID: {protocol.id} | {protocol.patient_name}</b>'
    )
        
    inline_keyboard = [[
        {
            'text': 'Постотреть протокол 🔎',
            'callback_data': f'prcl_{protocol.id}_1'
        }
    ]]
    
    reply_markup = {'inline_keyboard': inline_keyboard}
        
    response = send_request_until_success(
        telegram_service.send_message(
            chat_id=protocol.doctor.telegram_id,
            text=text,
            reply_markup=reply_markup
        ) 
    )
    
    return response.status_code
            
        
@shared_task(ignore_result=True)
def set_notifications():
    now = timezone.now()
    unnotificated_drugs = get_unnotificated_drugs()
            
    for drug in unnotificated_drugs:
        datetime_to_take = timezone.make_aware(
            timezone.datetime.combine(
                now.date(),
                drug.time_to_take
            )
        ) 
        is_complete_take_button_sent = set_before_time_to_take_tasks(
            drug, now, datetime_to_take
        )
        drug.notifications_calendar[now.strftime('%d.%m.%Y')] = True
        
        if not is_complete_take_button_sent:
            continue
        
        set_after_time_to_take_tasks(drug, now, datetime_to_take)
        
    if unnotificated_drugs:
        Drug.objects.bulk_update(unnotificated_drugs, ['notifications_calendar'])
        
        
def set_before_time_to_take_tasks(
    drug: Drug,
    now: date,
    datetime_to_take: datetime
) -> bool:
    
    is_complete_take_button_sent = False
        
    for minutes_before in settings.SEND_REMINDER_MINUTES_BEFORE_TIME_TO_TAKE:
        notification_time = datetime_to_take - timedelta(minutes=minutes_before)
        if now > notification_time:
            continue
            
        eta = now + timedelta(seconds=(notification_time - now).total_seconds())
        send_reminder_kwargs = {'drug_id': drug.id, 'minutes_before': minutes_before}
            
        if minutes_before == settings.SEND_REMINDER_MINUTES_BEFORE_TIME_TO_TAKE[-1]:
            call_patient_before_time_to_take.apply_async(
                args=(drug.id,),
                eta=eta + timedelta(seconds=5)
            )
            send_reminder_kwargs['add_complete_take_button'] = True
            is_complete_take_button_sent = True
                
        send_reminder_before_time_to_take.apply_async(
            kwargs=send_reminder_kwargs,
            eta=eta
        )
    
    return is_complete_take_button_sent
       

def set_after_time_to_take_tasks(
    drug: Drug,
    now: date,
    datetime_to_take: datetime
) -> None:       
    for i in range(1, settings.REMNDERS_COUNT_AFTER_TIME_TO_TAKE+1):  # 3 напоминания по 5 минут каждое
        notification_time = datetime_to_take + timedelta(
            minutes=i * settings.SEND_REMINDER_MINUTE_AFTER_TIME_TO_TAKE
        ) 
        if now > datetime_to_take:
            continue
            
        eta = now + timedelta(seconds=(notification_time - now).total_seconds())
        send_reminder_after_time_to_take.apply_async(
            args=(drug.id,),
            eta=eta
        )
            
        if i == settings.REMNDERS_COUNT_AFTER_TIME_TO_TAKE:
            eta += timedelta(seconds=30)
            notify_doctor_about_drug_take_miss.apply_async(
                args=(drug.id,),
                eta=eta
        )
