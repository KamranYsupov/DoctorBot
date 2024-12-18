import requests
from django.conf import settings


class SMSCService:
    def __init__(
        self,
        login: str = settings.SMSC_LOGIN,
        psw: str = settings.SMSC_PASSWORD,
    ):
        self.login = login
        self.__psw = psw
        
    def create_call(
        self,
        phone: str,
        message: str,
        seconds_to_wait: int = 25,
        repeat_interval: int = 0,
        call_attemps: int = 1,
    ):
        params = {
            'login': self.login,
            'psw': self.__psw,
            'phones': phone,
            'mes': message,
            'call': 1,
            'param': (
                f'{seconds_to_wait},{repeat_interval},{call_attemps}'
            )
        }

        response = requests.get(
            settings.SMSC_CREATE_CALL_URL,
            params=params
        )

        return response
    
      
        
smsc_service = SMSCService()