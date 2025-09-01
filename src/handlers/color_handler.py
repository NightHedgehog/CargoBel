from bson import ObjectId

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.database.connection import connection
from src.keyboards.color_keyboard import color_keyboard
from src.keyboards.price_keyboard import price_keyboard
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

@router.message(StateFilter(OrderStates.color), F.text)
async def handle_color(message: Message, state: FSMContext):
    color_text = message.text.strip()
    if not color_text or len(color_text) > 100:
        await message.answer(
            "⚠ Введите цвет/характеристику. Пример: Синий и белый, металлический корпус",
            reply_markup=color_keyboard(back_cb="back_to_size"),
        )
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    item_index = int(data.get("item_index", 0))

    await orders.update_one(
        {"_id": _oid(order_id)},
        {"$set": {f"items.{item_index}.color": color_text}},
    )

    item = await _get_item(order_id, item_index)
    await state.set_state(OrderStates.price)
    await message.answer(
        f"{_item_caption(item)}\n\n"
        "💰 Теперь пришлите цену в юанях ¥\n\n"
        "❗️Цена указана в карточке товара. Пришлите то значение, что видите там.\n"
        "⚠️ На некоторых сайтах при выборе >1 позиции цена может меняться!\n\n"
        "📌 Пример: 399, 12, 599.20",
        reply_markup=price_keyboard(back_cb="back_to_color"),
        disable_web_page_preview=True,
    )


@router.message(StateFilter(OrderStates.color))
async def handle_color_invalid(message: Message):
    await message.answer(
        "⚠ Отправьте текст с цветом/характеристикой. Пример: Синий и белый",
        reply_markup=color_keyboard(back_cb="back_to_size"),
    )

@router.callback_query(F.data == "back_to_color")
async def back_to_color(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.color)
    await callback.message.edit_text(
        "🎨 Теперь пришлите Цвет товара или другие характеристики\n\n"
        "📌 Пример: Синий и белый, металлический корпус",
        reply_markup=color_keyboard(back_cb="back_to_size"),
    )
    await callback.answer()
