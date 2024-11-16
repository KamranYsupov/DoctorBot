from datetime import timedelta

import loguru
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .models import Protocol
from web.utils.telegram_service import send_messsage


@shared_task
def send_notification(protocol_id):
    protocol = Protocol.objects.get(id=protocol_id)
    telegram_id = protocol.patient.telegram_id
    
    drugs_string = ', '.join(protocol.drugs)
    text = f'Осталось {minutes_before} \
        минут до приема лекарств: <em>{drugs_string}</em>'
    
    inline_keyboard = [[
        {
            'text': 'Выполнено',
            'callback_data': f'complete_protocol_{protocol_id}'
        }
    ]]
    
    reply_markup = {'inline_keyboard': inline_keyboard}
    
    response = send_messsage(
        chat_id=telegram_id,
        text=text, 
        reply_markup=reply_markup,
    )
    
    return response.status_code
    

@shared_task
def send_reminder(protocol_id):
    protocol = Protocol.objects.get(id=protocol_id)
    telegram_id = protocol.patient.telegram_id
    
    drugs_string = ', '.join(protocol.drugs)
    text = f'Напоминаем, что \
        пора принять лекарства: {drugs_string}'

    response = send_messsage(
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
        .filter(last_take__gte=now.date(), patient__isnull=False)
        .select_related('doctor', 'patient')
    ) # Достаем только те протоколы, которые ещё не истекли
    loguru.logger.info(f'Current: {current_protocols}')
    unnotificated_protocols = [
        protocol for protocol in current_protocols 
        if protocol.notifications_calendar[current_date_strformat] == False
    ] # Протоколы, по которым еще нет задач с уведомлением
    
    loguru.logger.info(str(unnotificated_protocols))
    for protocol in unnotificated_protocols:
        time_to_take = timezone.make_aware(
            timezone.datetime.combine(
                now.date(),
                protocol.time_to_take
            )
        )
        if time_to_take > now:
            for minutes_before in [15, 5]:
                notification_time = time_to_take - timedelta(minutes=minutes_before)
                send_notification.apply_async(
                    args=[protocol.id], 
                    eta=notification_time
                )

        
        reminder_start_time = time_to_take
        for i in range(1, 7):  # 6 напоминаний по 5 минут каждое
            reminder_time = reminder_start_time + timedelta(minutes=i * 5)
            send_reminder.apply_async(args=[protocol.id], eta=reminder_time)
            
        protocol.notifications_calendar[current_date_strformat] = True
        
    if unnotificated_protocols:
        Protocol.objects.bulk_update(unnotificated_protocols, ['notifications_calendar'])
        
    return unnotificated_protocols