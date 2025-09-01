from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import settings

def photo_keyboard(back_cb: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Инструкция, где найти ссылку", url=settings.INSTRUCTION_CHANNEL_ID)],
            [InlineKeyboardButton(text="👨 Связь с Менеджером", url=settings.INSTRUCTION_CHANNEL_ID)],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=back_cb)],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]
    )
