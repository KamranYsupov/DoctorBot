import asyncio
import os

import django
import loguru
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv


async def main():
    """Запуск бота"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.core.settings')

    django.setup()

    load_dotenv()

    from core import config
    from middlewares.throttling import rate_limit_middleware
    from handlers.routing import get_main_router


    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties())
    dp = Dispatcher()
    
    try:
        dp.message.middleware(rate_limit_middleware)
        dp.include_router(get_main_router())
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':
    loguru.logger.info('Bot is starting')
    asyncio.run(main())
