from __future__ import annotations

import re
from bson import ObjectId

from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.states.price import OrderStates
from src.keyboards.link_keyboard import link_keyboard
from src.keyboards.size_keyboard import size_keyboard
from src.database.connection import connection

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

URL_RE = re.compile(r"(?i)\b((?:https?://|www\.)[^\s]+)")

def _normalize_url(text: str) -> str | None:
    m = URL_RE.search(text or "")
    if not m:
        return None
    url = m.group(1)
    if url.startswith("www."):
        url = "https://" + url
    return url

# ========== ожидание ссылки ==========
@router.message(StateFilter(OrderStates.link), F.text)
async def handle_link_input(message: types.Message, state: FSMContext):
    url = _normalize_url(message.text.strip())
    if not url:
        await message.answer(
            "⚠ Пожалуйста, пришлите корректную ссылку на товар (начинается с http:// или https://).",
            reply_markup=link_keyboard(back_cb="back_to_photo"),
        )
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    item_index = int(data.get("item_index", 0))

    try:
        oid = ObjectId(order_id)
    except Exception:
        await message.answer("😬 Не удалось сохранить ссылку. Попробуйте ещё раз.")
        return

    # сохраняем ссылку в текущий item
    await orders.update_one(
        {"_id": oid},
        {"$set": {f"items.{item_index}.link": url}},
        upsert=False,
    )

    # ✨ достаём item, чтобы показать сводку именно с ссылкой
    item = await _get_item(order_id, item_index)

    await message.answer(
        f"{_item_caption(item)}\n\n"
        "📏 Теперь пришлите размер (одежды или обуви) или другую характеристику (для иных товаров)\n\n"
        "❗️Чтобы правильно выбрать размер, нужно посмотреть размерную сетку конкретного продавца.\n"
        "❗️Как найти размерную сетку и правильно подобрать размер — смотрите в инструкциях.\n\n"
        "📌 Пример: 43, M, L, 42.5",
        reply_markup=size_keyboard(back_cb="back_to_link"),
        disable_web_page_preview=True,
    )
    await state.set_state(OrderStates.size)



# Если пришёл не текст (стикер, фото и т.п.) — просим именно ссылку
@router.message(StateFilter(OrderStates.link))
async def handle_link_invalid(message: types.Message):
    await message.answer(
        "⚠ Пожалуйста, отправьте текстовую ссылку на товар. Пример: https://item.taobao.com/…",
        reply_markup=link_keyboard(back_cb="back_to_photo"),
    )

# Назад из шага "размер" — вернуться к шагу "ссылка"
@router.callback_query(F.data == "back_to_link")
async def back_to_link(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.link)
    await callback.message.edit_text(
        "🔗 Теперь пришлите ссылку на товар\n\n"
        "❗️Если не знаете, как найти и скопировать ссылку на сайте, "
        "обратитесь к инструкции ниже или спросите у нашего менеджера.",
        reply_markup=link_keyboard(back_cb="back_to_photo"),
    )
    await callback.answer()