# from aiogram import Bot
# from aiogram.fsm.context import FSMContext
# from aiogram.types import CallbackQuery, Message
#
# from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
# from src.telegram.keyboards.inline import keyboards_text
# from src.telegram import texts
#
#
# async def get_call_answer(message: Message, state: FSMContext):
#     main_state = await state.get_state().split(":")[1]
#     response = await state.get_data().get("data")
#
#     await message.answer(
#         text=,
#         reply_markup=create_vertical_keyboard(
#             keyboards_text.chose_language_post_buttons
#         ),
#     )
