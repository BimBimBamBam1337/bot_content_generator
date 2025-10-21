from aiogram.fsm.state import StatesGroup, State


class Promo(StatesGroup):
    got_code = State()


class Chat(StatesGroup):
    send_message = State()


class SendResponse(StatesGroup):
    prepare_reels = State()
    reels = State()
    telegram = State()
    instagram = State()
    threads = State()
    article = State()


class GenerateSemantic(StatesGroup):
    forward_1 = State()
    forward_2 = State()
    alcove = State()
    confirmed_main_goal = State()
