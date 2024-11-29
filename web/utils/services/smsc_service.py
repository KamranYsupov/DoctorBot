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
        
    def create_call(self, phone: str, message: str):
        params = {
            'login': self.login,
            'psw': self.__psw,
            'phones': phone,
            'mes': message,
            'call': 1  
        }

        response = requests.get(url, params=params)

        return response
      
        
smsc_service = SMSCService()