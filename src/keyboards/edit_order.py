from aiogram.utils.keyboard import InlineKeyboardBuilder

def edit_order_kb(items_count: int):
    kb = InlineKeyboardBuilder()
    for i in range(items_count):
        kb.button(text=f"✏️ Заполнить позицию {i+1}", callback_data=f"edit_item:{i}")
    kb.button(text="🏠 Меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()
