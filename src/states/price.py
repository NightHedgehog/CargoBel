from aiogram.fsm.state import StatesGroup, State

class OrderStates(StatesGroup):
    link = State()
    photo = State()
    size = State()
    color = State()
    price = State()
    quantity = State()
    confirm = State()
