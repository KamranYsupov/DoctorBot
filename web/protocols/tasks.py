import time
from datetime import timedelta

import loguru
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .models import Protocol
from web.utils.telegram_service import telegram_service


@shared_task
def send_reminder_before_time_to_take(
    protocol_id: int,
    minutes_before: int,
    sleep: int | float
):
    time.sleep(sleep)
    protocol = Protocol.objects.get(id=protocol_id)
    telegram_id = protocol.patient.telegram_id
    
    drugs_string = ', '.join(protocol.drugs)
    text = f'Осталось {minutes_before} '\
       f'минут до приема лекарств: <em>{drugs_string}</em>'
    
    inline_keyboard = [[
        {
            'text': 'Выполнено',
            'callback_data': f'complete_protocol_{protocol_id}'
        }
    ]]
    
    reply_markup = {'inline_keyboard': inline_keyboard}
    
    response = telegram_service.send_messsage(
        chat_id=telegram_id,
        text=text, 
        reply_markup=reply_markup,
    )
    
    return response.status_code
    

@shared_task
def send_reminder_after_time_to_take(protocol_id: int, sleep: int | float):
    time.sleep(sleep)
    protocol = Protocol.objects.get(id=protocol_id)
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    if protocol.reception_calendar[current_date_strformat]:
        return 
        
    telegram_id = protocol.patient.telegram_id
    
    drugs_string = ', '.join(protocol.drugs)
    text = f'Напоминаем, что ' \
        f'пора принять лекарства: {drugs_string}'

    response = telegram_service.send_messsage(
        chat_id=telegram_id,
        text=text, 
    )
    
    return response.status_code
    
         
@shared_task
def schedule_notifications():
    now = timezone.now()
    current_date_strformat = now.strftime('%d.%m.%Y')
    current_protocols = (
        Protocol.objects
        .filter(
            first_take__lte=now.date(),
            last_take__gte=now.date(),
            patient__isnull=False,
        )
        .select_related('doctor', 'patient')
    ) # Достаем только активные на сегодняшнее число протоколы

    unnotificated_protocols = [
        protocol for protocol in current_protocols
        if protocol.notifications_calendar.get(current_date_strformat) == False
    ] # Протоколы, по которым еще нет задач с уведомлением
        
    for protocol in unnotificated_protocols:
        time_to_take = timezone.make_aware(
            timezone.datetime.combine(
                now.date(),
                protocol.time_to_take
            )
        )
                
        for minutes_before in (15, 5):
            notification_time = time_to_take - timedelta(minutes=minutes_before)
            if now > notification_time:
                continue
            
            sleep = (notification_time - now).total_seconds()
            send_reminder_before_time_to_take.delay(
                protocol.id, 
                minutes_before,
                sleep
            )

        
        for i in range(1, 7):  # 6 напоминаний по 5 минут каждое
            reminder_time = time_to_take + timedelta(minutes=i * 5) 
            
            sleep = (reminder_time - now).total_seconds()
            send_reminder_after_time_to_take.delay(
                protocol.id,
                sleep
            )
            
        protocol.notifications_calendar[current_date_strformat] = True
        
    if unnotificated_protocols:
        Protocol.objects.bulk_update(unnotificated_protocols, ['notifications_calendar'])
        