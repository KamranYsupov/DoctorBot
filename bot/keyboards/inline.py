from typing import Dict, Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from core import config


def get_inline_keyboard(*, buttons: Dict[str, str], sizes: Tuple = (1, 2)):
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def get_menu_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text='Протоколы 🗂️',
            callback_data='protocols_1'
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text='FAQ ❔',
            callback_data='faq'
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text='Связатся с менеджером ☎',
            url=config.MANAGER_ACCOUNT_LINK,
        )
    )
    
    return keyboard.adjust(1, 1, 1).as_markup()


def get_protocol_inline_button_keyboard(
    protocol_id: int,
    page_number: int = 1,
):
    buttons = {'Вернутся к протоколу 🔙': f'protocol_{protocol_id}_{page_number}'}
    
    return get_inline_keyboard(buttons=buttons)


inline_cancel_keyboard = get_inline_keyboard(
    buttons={'Отмена ❌': 'cancel'}
)
