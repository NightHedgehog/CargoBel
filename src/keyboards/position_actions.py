from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def position_actions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить ещё товар", callback_data="add_more_item")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="submit_order")],
            [InlineKeyboardButton(text="⚙️ Редактировать заказ", callback_data="edit_order")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]
    )
