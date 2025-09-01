from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.database.connection import connection
from src.keyboards.main_keyboard import main_menu, reviews_menu, calc_intro_keyboard

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router()
users_collection = connection["users"]


# 📥 /start
@router.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        await users_collection.insert_one({"_id": user_id})
        await message.reply(
            "👋 Привет! Я бот для заказа товаров из Китая\n"
            "Выбери действие ниже 👇",
            reply_markup=main_menu()
        )
    else:
        await message.reply(
            "👋 С возвращением! Я бот для заказа товаров из Китая\n"
            "Выбери действие ниже 👇",
            reply_markup=main_menu()
        )

# Кнопка 🏠 Отзывы
@router.callback_query(F.data == "reviews_menu")
async def open_reviews_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "⭐ Отзывы\n\nВыберите действие:",
        reply_markup=reviews_menu()
    )
    await callback.answer()

# Кнопка 🏠 Меню
@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )


# Кнопка 📦 Рассчитать стоимость
@router.callback_query(F.data == "calc_cost")
async def start_cost_calc(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Для расчёта стоимости у вас должно быть установлено китайское приложение "
        "Taobao, Poison, Duodenum или другое и обязательно пройдена регистрация через номер телефона.\n\n"
        "Без регистрации вы не сможете рассчитать стоимость, посмотреть цену, выбрать размер и многое другое.",
        reply_markup=calc_intro_keyboard()
    )


# Кнопка 🔙 Назад
@router.callback_query(F.data == "calc_back_to_intro")
async def back_to_intro(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Для расчёта стоимости у вас должно быть установлено китайское приложение "
        "Taobao, Poison, Duodenum или другое и обязательно пройдена регистрация через номер телефона.\n\n"
        "Без регистрации вы не сможете рассчитать стоимость, посмотреть цену, выбрать размер и многое другое.",
        reply_markup=calc_intro_keyboard()
    )
