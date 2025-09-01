from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import settings

def link_keyboard(back_cb: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Инструкция, где найти ссылку", url=settings.INSTRUCTION_CHANNEL_ID)],
            [InlineKeyboardButton(text="👨 Менеджер", url=settings.MANAGER_USERNAME)],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=back_cb)],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")]
        ]
    )