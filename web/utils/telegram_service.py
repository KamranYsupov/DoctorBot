import requests
import json
from django.conf import settings


def send_messsage(
    chat_id: int,
    text: str,
    reply_markup: dict[str, list] | None = None,
    parse_mode: str = 'HTML',
):
    headers = {'Content-Type': 'application/json'}
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
        'reply_markup': json.dumps(reply_markup) if reply_markup else None,
    }
    
    response = requests.post(
        settings.TELEGRAM_API_URL, 
        data=json.dumps(payload),
        headers=headers
    )
    
    return response

