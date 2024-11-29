from asgiref.sync import sync_to_async

from web.protocols.models import Protocol
from web.drugs.models import Drug


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
def get_protocol_info_message(protocol: Protocol) -> str:
    message_info = (
    f'<b>Протокол ID:</b> {protocol.id}\n\n'
    f'<b>Препараты:</b>'
    )
    
    for drug in protocol.drugs.all():
        message_info += '\n\n' 
        message_info += get_drug_info_message(drug)
    
    return message_info


default_process_time_to_take_message = (
    'Отправьте сообщение в формате <em><b>{час}:{минута}</b></em>.\n'
    '<b>Пример:</b> <b><em>12:35</em></b>\n\n'
    '<b>Важно! Время должно быть в МСК</b>'
)