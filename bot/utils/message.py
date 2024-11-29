from core import config

from asgiref.sync import sync_to_async

from models import Drug, Protocol


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


default_process_time_to_take_message = (
    'Отправьте сообщение в формате <em><b>{час}:{минута}</b></em>.\n'
    '<b>Пример:</b> <b><em>12:35</em></b>\n\n'
    '<b>Важно! Время должно быть в МСК</b>'
)