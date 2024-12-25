from asgiref.sync import sync_to_async
from django.utils import timezone
from django.conf import settings

from core import config
from models import Drug, Protocol
from utils.pagination import Paginator

from datetime import datetime, timedelta, date, time
from typing import List, Dict


def get_drug_info_message(drug: Drug) -> str:
    message_info = (
        f'<b>Название:</b> <b>{drug.name}</b>\n'
        f'<b>Дата первого приема:</b> {drug.first_take.strftime("%d.%m.%Y")}\n' 
        f'<b>Срок приема: </b>'
        f'<em>{drug.first_take.strftime("%d.%m.%Y")} '
        f'- {drug.last_take.strftime("%d.%m.%Y")}</em>\n' 
        f'<b>Время приема:</b> {drug.time_to_take.strftime("%H:%M")}'
    )
    
    return message_info


@sync_to_async
def get_protocol_info_message(
    protocol: Protocol, 
    add_link: bool = False
) -> str:
    message_info = (
    f'<b>Протокол ID:</b> {protocol.id}\n\n'
    f'<b>Препараты:</b>'
    )
    
    for drug in protocol.drugs.all():
        message_info += '\n\n' 
        message_info += get_drug_info_message(drug)
        
    if add_link:
        protocol_start_link = f'{config.BOT_LINK}?start={protocol.id}'    
        message_info += f'\n\n<b>Ссылка для пациента</b>: {protocol_start_link}'
    
    return message_info


def get_protocol_statistic_message(
    dates: List[str], 
    general_reception_calendar: Dict[str, bool]
) -> str:
    message_text = ''
    current_drug_id = None
    now = timezone.now()
        
    for string_data in dates:
        drug_id = string_data.split('赛')[0]
        date = string_data.split('赛')[-1]
        
        if current_drug_id != drug_id:
            current_drug_id = drug_id
            
            time_to_take = string_data.split('赛')[-2]
            datetime_string = f'{time_to_take} {date}'
            take_miss_datetime = timezone.make_aware(
                datetime.strptime(datetime_string, '%H:%M:%S %d.%m.%Y') \
                + timedelta(minutes=settings.PROTOCOL_DRUGS_TAKE_INTERVAL)
            )
            
            drug_name = string_data.split('赛')[-3]
            message_text += f'\n<b>{drug_name}</b>\n\n'
        
        
        if general_reception_calendar[string_data]:
            status_str = 'Выполнен ✅ '
        elif general_reception_calendar[string_data] == False:
            status_str = 'Пропущен ❌'
        else:
            status_str = 'Не выполнен'

        message_text += f'{date}: <b>{status_str}</b>\n'
        
    return message_text


default_process_time_to_take_message = (
    'Отправьте сообщение в формате <em><b>{час}:{минута}</b></em>.\n'
    '<b>Пример:</b> <b><em>12:35</em></b>\n\n'
    '<b>Важно! Время должно быть в МСК</b>'
)


