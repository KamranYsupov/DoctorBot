from typing import Sequence

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)


def get_reply_keyboard(
    buttons: Sequence[str],
    resize_keyboard: bool = True,
) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=button_text)] for button_text in buttons]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=resize_keyboard
    )
    

reply_keyboard_remove = ReplyKeyboardRemove()