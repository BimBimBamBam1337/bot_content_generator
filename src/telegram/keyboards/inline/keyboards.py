from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_vertical_keyboard(keyboards: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=value[0], callback_data=value[1])]
            for value in keyboards.values()
        ]
    )
