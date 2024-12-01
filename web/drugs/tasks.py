import asyncio
from datetime import timedelta

import loguru
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from asgiref.sync import sync_to_async

from .models import Drug
from web.utils.telegram_service import (
    telegram_service,
    send_message_until_success,
)


@shared_task(ignore_result=True)
def send_reminder_before_time_to_take(
    drug_id: int, 
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
        text += f'Осталась <b>{minutes_before} минута</b>' 
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

    return send_message_until_success(
        chat_id=telegram_id,
        text=text,
        reply_markup=reply_markup,
    )
    

@shared_task(ignore_result=True)
def send_reminder_after_time_to_take(drug_id: int):
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
        
    return send_message_until_success(
        chat_id=telegram_id,
        text=text,
    )
    

@shared_task(ignore_result=True)
def notify_doctor_about_drug_take_miss(drug_id: int):
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

    if now > datetime_to_take + timedelta(
        minutes=settings.PROTOCOL_DRUGS_TAKE_INTERVAL
    ) and not drug.reception_calendar.get(current_date_strformat):
        text = (
            f'Пациент {protocol.patient_name} '
            f'пропустил приём <b><em>{drug.name}</em></b> по протоколу ' 
            f'<b>ID: {protocol.id} | {protocol.patient_name}</b>'
        )
        
        inline_keyboard = [[
            {
                'text': 'Постотреть протокол 🔎',
                'callback_data': f'protocol_1_{protocol.id}'
            }
        ]]
    
        reply_markup = {'inline_keyboard': inline_keyboard}
        
        return send_message_until_success(
            chat_id=protocol.doctor.telegram_id,
            text=text,
            reply_markup=reply_markup
        )
        

@shared_task(ignore_result=True)
def set_notifications():
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    current_drugs = Drug.objects.select_related(
        'protocol',
        'protocol__patient',
        'protocol__doctor'
    ).filter(
        first_take__lte=now.date(),
        last_take__gte=now.date(),
        protocol__patient__isnull=False,
    )
    
    
    unnotificated_drugs = [
        drug for drug in current_drugs
        if drug.notifications_calendar.get(current_date_strformat) == False
    ]
            
    for drug in unnotificated_drugs:
        datetime_to_take = timezone.make_aware(
            timezone.datetime.combine(
                now.date(),
                drug.time_to_take
            )
        )       
        
        for minutes_before in settings.SEND_REMINDER_MINUTES_BEFORE_TIME_TO_TAKE:
            notification_time = datetime_to_take - timedelta(minutes=minutes_before)
            if now > notification_time:
                continue
            
            eta = now + timedelta(seconds=(notification_time - now).total_seconds())
            send_reminder_kwargs = {'drug_id': drug.id, 'minutes_before': minutes_before}
            
            if minutes_before == settings.SEND_REMINDER_MINUTES_BEFORE_TIME_TO_TAKE[-1]:
                send_reminder_kwargs['add_complete_take_button'] = True
                
            send_reminder_before_time_to_take.apply_async(
                kwargs=send_reminder_kwargs,
                eta=eta
            )
        
        for i in range(1, settings.REMNDERS_COUNT_AFTER_TIME_TO_TAKE+1):  # 3 напоминания по 5 минут каждое
            notification_time = datetime_to_take + timedelta(
                minutes=i * settings.SEND_REMINDER_MINUTE_AFTER_TIME_TO_TAKE
            ) 
            if now > notification_time:
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
            
        drug.notifications_calendar[current_date_strformat] = True
    
    if unnotificated_drugs:
        Drug.objects.bulk_update(unnotificated_drugs, ['notifications_calendar'])
