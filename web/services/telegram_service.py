import json

import loguru
import requests
from django.conf import settings


class TelegramService:
    def __init__(
        self,
        bot_token: str = settings.BOT_TOKEN,
        api_url: str = settings.TELEGRAM_API_URL
    ):
        self.__bot_token = bot_token
        self.api_url = api_url
       
    @property
    def __bot_api_url(self):
        return f'{self.api_url}/bot{self.__bot_token}'
        
    def send_message(
        self,
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
        }
    
        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)
    
        response = requests.post(
            url=f'{self.__bot_api_url}/sendMessage', 
            data=json.dumps(payload),
            headers=headers
        )
    
        return response

        
telegram_service = TelegramService()


def send_message_until_success(
    chat_id: int,
    text: str,
    reply_markup: dict[str, list] | None = None,
    parse_mode: str = 'HTML',
) -> int:
    status_code = 1
    
    while status_code != 200:
        try:
            response = telegram_service.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
            )
        except requests.exceptions.ConnectTimeout:
            continue
        
        status_code = response.status_code
    
    return status_code
