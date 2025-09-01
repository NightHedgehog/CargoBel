from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.keyboards.photo_keyboard import photo_keyboard
from src.keyboards.link_keyboard import link_keyboard
from src.database.connection import connection
from src.states.price import OrderStates

router = Router()

orders = connection["orders"]

# Кнопка ✅ Продолжить
@router.callback_query(F.data == "calc_continue")
async def send_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.photo)
    await callback.message.edit_text(
        "✅ Отлично!\n"
        "📸 Теперь пришлите фото товара\n"
        "⚙️ Нажмите на значок 📎 и выберите “Фото”\n\n"
        "❗️Сделайте скрин товара и пришлите сюда\n"
        "❗️Должна быть видна расцветка\n"
        "❗️Набор поставки или другие важные характеристики",
        reply_markup=photo_keyboard(back_cb="calc_back_to_intro")
    )

# Если прислали фото
@router.message(OrderStates.photo, F.photo)
async def on_photo_ok(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id  # самое большое превью

    # Добавляем элемент в массив items через $push, при upsert задаём базовые поля
    await orders.update_one(
        {"user_id": user_id, "status": "draft"},
        {
            "$setOnInsert": {"user_id": user_id, "status": "draft"},
            "$push": {
                "items": {
                    "photo_file_id": photo_id,
                    "link": None,
                    "size": None,
                    "color": None,
                    "price_cny": None,
                    "qty": None,
                }
            },
        },
        upsert=True,
    )

    # Получим обновлённый черновик, чтобы знать индекс позиции
    draft = await orders.find_one({"user_id": user_id, "status": "draft"}, projection={"items": 1})
    item_index = len(draft.get("items", [])) - 1

    # Сохраним id заказа и индекс позиции в FSM
    await state.update_data(order_id=str(draft["_id"]), item_index=item_index)

    # Переходим к шагу "ссылка"
    await state.set_state(OrderStates.link)
    await message.answer(
        "📸 Фото добавлено\n\n"
        "🔗 Теперь пришлите ссылку на товар\n\n"
        "❗️Если не знаете, как найти и скопировать ссылку на сайте, "
        "воспользуйтесь инструкцией ниже или напишите менеджеру.",
        reply_markup=link_keyboard(back_cb="back_to_photo"),
    )

# Если прислали не фото
@router.message(OrderStates.photo)
async def on_photo_invalid(message: Message) -> None:
    await message.answer(
        "⚠️ Пожалуйста, прикрепите именно фото.\n"
        "⚙️ Нажмите на значок 📎 и выберите «Фото».",
        reply_markup=photo_keyboard(back_cb="calc_back_to_intro"),
    )


# Назад из шага "ссылка" — возвращаемся к шагу "фото"
@router.callback_query(F.data == "back_to_photo")
async def back_to_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.photo)
    await callback.message.edit_text(
        "✅ Отлично!\n"
        "📸 Теперь пришлите фото товара\n"
        "⚙️ Нажмите на значок 📎 и выберите «Фото»\n\n"
        "❗️Сделайте скрин товара и пришлите сюда\n"
        "❗️Должна быть видна расцветка\n"
        "❗️Набор поставки или другие важные характеристики",
        reply_markup=photo_keyboard(back_cb="calc_back_to_intro"),
    )
    await callback.answer()