from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import settings


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Личный кабинет", callback_data="personal_area")
    builder.button(text="📦 Рассчитать стоимость", callback_data="calc_cost")
    builder.button(text="💬 Связь с менеджером", url=settings.MANAGER_USERNAME)
    builder.button(text="📚 Инструкции", url=settings.INSTRUCTION_CHANNEL_ID)
    builder.button(text="⭐ Отзывы", callback_data="reviews_menu")
    builder.adjust(2)
    return builder.as_markup()

def reviews_menu():
    """Меню отзывов"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Посмотреть отзывы", url=settings.REVIEWS_CHANNEL_ID)
    builder.button(text="🫂 Оставьте отзыв и получите скидку", url=settings.REVIEWS_GROUP_ID)
    builder.button(text="🏠 Меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def calc_intro_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Продолжить", callback_data="calc_continue")],
            [InlineKeyboardButton(text="📚 Инструкции", url=settings.INSTRUCTION_CHANNEL_ID)],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]
    )
