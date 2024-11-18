import os

from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
BOT_LINK = f'https://t.me/{BOT_USERNAME}'

QR_CODE_API_GENERATOR_URL = 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data='