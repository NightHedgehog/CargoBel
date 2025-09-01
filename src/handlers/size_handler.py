from bson import ObjectId

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.database.connection import connection
from src.keyboards.color_keyboard import color_keyboard
from src.keyboards.size_keyboard import size_keyboard
from src.states.price import OrderStates

router = Router()

orders = connection["orders"]

def _oid(s: str) -> ObjectId:
    return ObjectId(str(s))


async def _get_item(order_id: str, item_index: int) -> dict | None:
    doc = await orders.find_one({"_id": _oid(order_id)}, projection={"items": 1})
    if not doc:
        return None
    items = doc.get("items", [])
    if 0 <= item_index < len(items):
        return items[item_index]
    return None


def _item_caption(item: dict) -> str:
    link = item.get("link") or "—"
    size = item.get("size") or "—"
    color = item.get("color") or "—"
    price = item.get("price_cny")
    price_str = f"{price} ¥" if price is not None else "—"
    qty = item.get("qty")
    qty_str = str(qty) if qty is not None else "—"

    return (
        "📸 Добавлено\n"
        f"🔗 Ссылка: {link}\n"
        f"📏 Размер: {size}\n"
        f"🎨 Цвет/характеристика: {color}\n"
        f"💰 Цена: {price_str}\n"
        f"🔢 Количество: {qty_str}"
    )


@router.message(StateFilter(OrderStates.size), F.text)
async def handle_size(message: Message, state: FSMContext):
    size_text = message.text.strip()
    if not size_text or len(size_text) > 50:
        await message.answer(
            "⚠ Введите размер/характеристику (например: 43, M, L, 42.5)",
            reply_markup=size_keyboard(back_cb="back_to_link"),
        )
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    item_index = int(data.get("item_index", 0))

    await orders.update_one(
        {"_id": _oid(order_id)},
        {"$set": {f"items.{item_index}.size": size_text}},
    )

    item = await _get_item(order_id, item_index)
    await state.set_state(OrderStates.color)
    await message.answer(
        f"{_item_caption(item)}\n\n"
        "🎨 Теперь пришлите Цвет товара или другие характеристики\n\n"
        "❗️Цвет может быть указан в карточке или опишите его самостоятельно.\n"
        "📌 Пример: Синий и белый, металлический корпус",
        reply_markup=color_keyboard(back_cb="back_to_size"),
        disable_web_page_preview=True,
    )


@router.message(StateFilter(OrderStates.size))
async def handle_size_invalid(message: Message):
    await message.answer(
        "⚠ Отправьте текст с размером/характеристикой. Пример: 43, M, L, 42.5",
        reply_markup=size_keyboard(back_cb="back_to_link"),
    )

@router.callback_query(F.data == "back_to_size")
async def back_to_size(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.size)
    await callback.message.edit_text(
        "📏 Теперь пришлите размер (одежды или обуви) или другую характеристику (для иных товаров)\n\n"
        "📌 Пример: 43, M, L, 42.5",
        reply_markup=size_keyboard(back_cb="back_to_link"),
    )
    await callback.answer()
