from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from bson import ObjectId
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from src.database.connection import connection
from src.keyboards.color_keyboard import color_keyboard
from src.keyboards.position_actions import position_actions
from src.keyboards.price_keyboard import price_keyboard
from src.keyboards.qty_keyboard import qty_keyboard
from src.keyboards.size_keyboard import size_keyboard
from src.states.price import OrderStates
from src.keyboards.photo_keyboard import photo_keyboard
from src.keyboards.link_keyboard import link_keyboard
from src.keyboards.edit_order import edit_order_kb
from src.keyboards.main_keyboard import main_menu
from src.utils.excel import build_order_xlsx
from config.settings import settings

router = Router()

orders = connection["orders"]
users = connection["users"]  # если ведёшь профиль пользователя


# ----------------- utils -----------------

def _oid(s: str) -> ObjectId:
    return ObjectId(str(s))

def _item_caption(item: Dict[str, Any]) -> str:
    link = item.get("link") or "—"
    size = item.get("size") or "—"
    color = item.get("color") or "—"
    price = item.get("price_cny")
    price_str = f"{price} ¥" if price is not None else "—"
    qty = item.get("qty")
    qty_str = str(qty) if qty is not None else "—"
    return (
        f"🔗 Ссылка: {link}\n"
        f"📏 Размер: {size}\n"
        f"🎨 Цвет/хар-ка: {color}\n"
        f"💰 Цена: {price_str}\n"
        f"🔢 Кол-во: {qty_str}"
    )

def _order_caption(order: Dict[str, Any]) -> str:
    lines = [f"🆕 Новый заказ от пользователя #{order.get('user_id')}"]
    for idx, it in enumerate(order.get("items", []), start=1):
        lines.append(f"\nПозиция {idx}:\n{_item_caption(it)}")
    return "\n".join(lines)

def _missing_field(it: dict) -> str | None:
    if not it.get("link"): return "link"
    if not it.get("size"): return "size"
    if not it.get("color"): return "color"
    if it.get("price_cny") is None: return "price"
    if it.get("qty") is None: return "qty"
    return None


# ----------------- submit / add more -----------------

@router.callback_query(F.data == "submit_order")
async def submit_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id

    # 1) Получаем draft
    draft = await orders.find_one({"user_id": user_id, "status": "draft"})
    if not draft or not draft.get("items"):
        await callback.message.edit_text("Пока нет позиций для оформления. Добавьте товар.", reply_markup=position_actions())
        await callback.answer()
        return

    # 2) Если есть незаполненные позиции — умно перекидываем на первый незаполненный шаг
    for i, it in enumerate(draft["items"]):
        miss = _missing_field(it)
        if miss:
            await state.update_data(order_id=str(draft["_id"]), item_index=i)
            if miss == "link":
                await state.set_state(OrderStates.link)
                await callback.message.edit_text(
                    f"Позиция {i+1} не заполнена: отсутствует ссылка.\n\n"
                    "🔗 Пришлите ссылку на товар.",
                    reply_markup=link_keyboard(back_cb="back_to_photo"),
                )
            elif miss == "size":
                await state.set_state(OrderStates.size)
                await callback.message.edit_text(
                    f"Позиция {i+1}: не указан размер/характеристика.\n\n"
                    "📏 Пришлите размер (например: 43, M, L, 42.5).",
                    reply_markup=size_keyboard(back_cb="back_to_link"),
                )
            elif miss == "color":
                await state.set_state(OrderStates.color)
                await callback.message.edit_text(
                    f"Позиция {i+1}: не указан цвет/характеристика.\n\n"
                    "🎨 Пришлите цвет (например: Синий и белый, металлический корпус).",
                    reply_markup=color_keyboard(back_cb="back_to_size"),
                )
            elif miss == "price":
                await state.set_state(OrderStates.price)
                await callback.message.edit_text(
                    f"Позиция {i+1}: не указана цена.\n\n"
                    "💰 Пришлите цену в юанях (например: 399 или 599.20).",
                    reply_markup=price_keyboard(back_cb="back_to_color"),
                )
            elif miss == "qty":
                await state.set_state(OrderStates.quantity)
                await callback.message.edit_text(
                    f"Позиция {i+1}: не указано количество.\n\n"
                    "🔢 Пришлите количество (например: 1, 4, 5).",
                    reply_markup=qty_keyboard(back_cb="back_to_price"),
                )
            await callback.answer()
            return

    # 3) Все позиции заполнены → формируем Excel и отправляем менеджеру
    user_doc = await users.find_one({"_id": user_id}) or {}
    xls_bytes = build_order_xlsx(draft, user_doc)
    caption = _order_caption(draft)

    msg = await bot.send_document(
        chat_id=settings.MANAGER_GROUP_ID,
        document=BufferedInputFile(xls_bytes, filename=f"order_{draft['_id']}.xlsx"),
        caption=caption
    )

    # 4) Помечаем заказ как submitted
    await orders.update_one(
        {"_id": draft["_id"]},
        {"$set": {
            "status": "submitted",
            "submitted_at": dt.datetime.utcnow(),
            "xlsx_file_id": msg.document.file_id if msg.document else None,
        }}
    )

    # 5) Пользователю подтверждение
    await callback.message.edit_text(
        "✅ Заказ отправлен менеджеру. "
        "Мы свяжемся с вами для уточнения деталей. Спасибо!",
        reply_markup=main_menu(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "add_more_item")
async def add_more_item(callback: CallbackQuery, state: FSMContext):
    """
    Начинаем новую позицию: переводим на шаг 'photo' и просим фото.
    Предыдущая позиция уже сохранена в draft.items.
    """
    await state.set_state(OrderStates.photo)
    await callback.message.edit_text(
        "➕ Добавляем ещё товар.\n\n"
        "📸 Пришлите фото товара.",
        reply_markup=photo_keyboard(back_cb="calc_back_to_intro"),
    )
    await callback.answer()


# ----------------- editing -----------------

@router.callback_query(F.data == "edit_order")
async def open_edit_order(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    draft = await orders.find_one({"user_id": user_id, "status": "draft"}, projection={"items": 1})
    if not draft or not draft.get("items"):
        await callback.message.edit_text("Черновик пуст. Добавьте хотя бы одну позицию.")
        await callback.answer()
        return
    await callback.message.edit_text(
        "Выберите позицию для заполнения/исправления:",
        reply_markup=edit_order_kb(len(draft["items"]))
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_item:"))
async def edit_item(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id
    draft = await orders.find_one({"user_id": user_id, "status": "draft"})
    if not draft or idx >= len(draft.get("items", [])):
        await callback.message.edit_text("Позиция не найдена.")
        await callback.answer()
        return

    it = draft["items"][idx]
    # какая часть отсутствует
    if not it.get("link"):
        need, new_state, kb = "link", OrderStates.link, link_keyboard(back_cb="back_to_photo")
        text = f"Позиция {idx+1}: пришлите ссылку на товар."
    elif not it.get("size"):
        need, new_state, kb = "size", OrderStates.size, size_keyboard(back_cb="back_to_link")
        text = f"Позиция {idx+1}: пришлите размер/характеристику (например: 43, M, L, 42.5)."
    elif not it.get("color"):
        need, new_state, kb = "color", OrderStates.color, color_keyboard(back_cb="back_to_size")
        text = f"Позиция {idx+1}: пришлите цвет/характеристику."
    elif it.get("price_cny") is None:
        need, new_state, kb = "price", OrderStates.price, price_keyboard(back_cb="back_to_color")
        text = f"Позиция {idx+1}: пришлите цену в юанях (например: 399 или 599.20)."
    elif it.get("qty") is None:
        need, new_state, kb = "qty", OrderStates.quantity, qty_keyboard(back_cb="back_to_price")
        text = f"Позиция {idx+1}: пришлите количество (например: 1, 4, 5)."
    else:
        # если всё заполнено — можно показать сводку и кнопки действий
        await callback.message.edit_text(f"Позиция {idx+1} уже заполнена:\n\n{_item_caption(it)}", reply_markup=position_actions())
        await callback.answer()
        return

    await state.update_data(order_id=str(draft["_id"]), item_index=idx)
    await state.set_state(new_state)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
