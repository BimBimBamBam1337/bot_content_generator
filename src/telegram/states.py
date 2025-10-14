from aiogram.fsm.state import StatesGroup, State


class Promo(StatesGroup):
    got_code = State()
