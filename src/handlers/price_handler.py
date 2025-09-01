import decimal

from bson import ObjectId

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.database.connection import connection
from src.keyboards.price_keyboard import price_keyboard
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


def _parse_price(s: str) -> float | None:
    s = s.strip().replace(",", ".")
    try:
        # используем Decimal для точности, храним как float для простоты
        val = float(decimal.Decimal(s))
        return val if val >= 0 else None
    except Exception:
        return None


@router.message(StateFilter(OrderStates.price), F.text)
async def handle_price(message: Message, state: FSMContext):
    price_val = _parse_price(message.text or "")
    if price_val is None:
        await message.answer(
            "⚠ Введите цену числом. Пример: 399 или 599.20",
            reply_markup=price_keyboard(back_cb="back_to_color"),
        )
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    item_index = int(data.get("item_index", 0))

    await orders.update_one(
        {"_id": _oid(order_id)},
        {"$set": {f"items.{item_index}.price_cny": price_val}},
    )

    item = await _get_item(order_id, item_index)
    await state.set_state(OrderStates.quantity)
    await message.answer(
        f"{_item_caption(item)}\n\n"
        "🔢 Теперь пришлите количество данного товара\n\n"
        "📌 Пример: 1, 4, 5",
        reply_markup=qty_keyboard(back_cb="back_to_price"),
        disable_web_page_preview=True,
    )


@router.message(StateFilter(OrderStates.price))
async def handle_price_invalid(message: Message):
    await message.answer(
        "⚠ Отправьте цену числом. Пример: 399 или 599.20",
        reply_markup=price_keyboard(back_cb="back_to_color"),
    )

@router.callback_query(F.data == "back_to_price")
async def back_to_price(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.price)
    await callback.message.edit_text(
        "💰 Теперь пришлите цену в юанях ¥\n\n"
        "📌 Пример: 399, 12, 599.20",
        reply_markup=price_keyboard(back_cb="back_to_color"),
    )
    await callback.answer()
