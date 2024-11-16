from web.protocols.models import Protocol


def get_protocol_info_message(protocol: Protocol) -> str:
    drugs_string = ', '.join(protocol.drugs)
    message_info = (
    f'<b>Протокол:</b>\n\n'
    f'<b>Препараты:</b> <em>{drugs_string}</em>\n'
    f'<b>Дата первого приема:</b> {protocol.first_take}\n' 
    f'<b>Срок приема: </b>'
    f'{protocol.first_take.strftime("%d.%m.%Y")}'
    f'- {protocol.last_take.strftime("%d.%m.%Y")} ({protocol.period} дней)\n' 
    f'<b>Время приема:</b> {protocol.time_to_take.strftime("%H:%M")}'
    )
    
    
    return message_info