import asyncio
from datetime import timedelta

import loguru
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from asgiref.sync import sync_to_async

from .models import Protocol
from web.utils.telegram_service import (
    telegram_service,
    send_message_until_success,
)


@shared_task(ignore_result=True)
def send_reminder_before_time_to_take(protocol_id: int, minutes_before: int):
    protocol = Protocol.objects.get(id=protocol_id)
    telegram_id = protocol.patient.telegram_id
    
    if protocol.reception_calendar.get(current_date_strformat):
        return 
    
    drugs_string = ', '.join(protocol.drugs)
    text = f'Осталось <b>{minutes_before} минут</b>'\
    f' до приема лекарств: <em>{drugs_string}</em>'
    
    inline_keyboard = [[
        {
            'text': 'Выполнено ✅',
            'callback_data': f'complete_protocol_{protocol_id}'
        }
    ]]
    
    reply_markup = {'inline_keyboard': inline_keyboard}

    return send_message_until_success(
        chat_id=telegram_id,
        text=text,
        reply_markup=reply_markup,
    )
    
    
@shared_task(ignore_result=True)
def send_reminder_after_time_to_take(protocol_id: int):
    protocol = Protocol.objects.get(id=protocol_id)
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    if protocol.reception_calendar.get(current_date_strformat):
        return 
    
    telegram_id = protocol.patient.telegram_id
    
    drugs_string = ', '.join(protocol.drugs)
    text = f'Напоминаем, что пора принять лекарства: {drugs_string}'
    
    status_code = 0
    
    return send_message_until_success(
        chat_id=telegram_id,
        text=text,
    )
    

@shared_task(ignore_result=True)
def set_notifications():
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    current_protocols = Protocol.objects.filter(
        first_take__lte=now.date(),
        last_take__gte=now.date(),
        patient__isnull=False,
    ).select_related('doctor', 'patient')
    
    unnotificated_protocols = []

    for protocol in current_protocols:
        if protocol.notifications_calendar.get(current_date_strformat) == False:
            unnotificated_protocols.append(protocol)
            
    for protocol in unnotificated_protocols:
        time_to_take = timezone.make_aware(
            timezone.datetime.combine(
                now.date(),
                protocol.time_to_take
            )
        )
        
        for minutes_before in settings.SEND_REMINDER_MINUTES_BEFORE_TIME_TO_TAKE:
            notification_time = time_to_take - timedelta(minutes=minutes_before)
            if now > notification_time:
                continue
            
            eta = now + timedelta(seconds=(notification_time - now).total_seconds())
            send_reminder_before_time_to_take.apply_async(
                args=(protocol.id, minutes_before),
                eta=eta
            )
        
        for i in range(1, 7):  # 6 напоминаний по 5 минут каждая
            reminder_time = time_to_take + timedelta(
                minutes=i * settings.SEND_REMINDER_MINUTE_AFTER_TIME_TO_TAKE
            ) 
            eta = now + timedelta(seconds=(reminder_time - now).total_seconds())
            send_reminder_after_time_to_take.apply_async(
                args=(protocol.id,),
                eta=eta
            )
            
        protocol.notifications_calendar[current_date_strformat] = True
    
    if unnotificated_protocols:
        Protocol.objects.bulk_update(unnotificated_protocols, ['notifications_calendar'])
