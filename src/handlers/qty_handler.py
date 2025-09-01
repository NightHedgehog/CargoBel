from bson import ObjectId

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.database.connection import connection
from src.keyboards.position_actions import position_actions
from src.keyboards.qty_keyboard import qty_keyboard
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


@router.message(StateFilter(OrderStates.quantity), F.text)
async def handle_quantity(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) < 1:
        await message.answer(
            "⚠ Введите количество целым числом ≥ 1. Пример: 1, 4, 5",
            reply_markup=qty_keyboard(back_cb="back_to_price"),
        )
        return
    qty = int(text)

    data = await state.get_data()
    order_id = data.get("order_id")
    item_index = int(data.get("item_index", 0))

    await orders.update_one(
        {"_id": _oid(order_id)},
        {"$set": {f"items.{item_index}.qty": qty}},
    )

    item = await _get_item(order_id, item_index)
    await state.set_state(OrderStates.confirm)

    # Итог по позиции + действия
    await message.answer(
        "Позиция 1:\n\n"  # если нужно — можно нумеровать по item_index + 1
        f"{_item_caption(item)}",
        reply_markup=position_actions(),
        disable_web_page_preview=True,
    )


@router.message(StateFilter(OrderStates.quantity))
async def handle_qty_invalid(message: Message):
    await message.answer(
        "⚠ Отправьте количество числом. Пример: 1, 4, 5",
        reply_markup=qty_keyboard(back_cb="back_to_price"),
    )
