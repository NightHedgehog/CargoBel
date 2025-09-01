from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import settings

def price_keyboard(back_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Инструкция: как определить цену", url=settings.INSTRUCTION_CHANNEL_ID)],
            [InlineKeyboardButton(text="👨 Если есть вопросы — менеджер", url=settings.MANAGER_USERNAME)],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=back_cb)],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]
    )