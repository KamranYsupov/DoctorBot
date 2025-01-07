import time
from typing import Dict, Coroutine

from loguru import logger
from aiogram.types import Message

from core import config 


async def rate_limit_middleware(
    handler: Coroutine,
    event: Message,
    data: Dict
):
    """Middleware для ограничения отправки сообщений пользователем боту."""

    user_id = event.from_user.id
    current_time = time.time()

    if not hasattr(rate_limit_middleware, 'users'):
        rate_limit_middleware.users = {}

    if user_id in rate_limit_middleware.users:
        last_message_time = rate_limit_middleware.users[user_id]

        if current_time - last_message_time < config.MAX_MESSAGE_PER_SECOND:
            return await event.answer('Слишком много сообщений! Попробуйте позже.')

    rate_limit_middleware.users[user_id] = current_time
    return await handler(event, data)
