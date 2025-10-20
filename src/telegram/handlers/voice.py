import os
import aiohttp

from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from src.database.uow import UnitOfWork
from src.telegram.states import Promo, Chat
from src.telegram import texts
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.keyboards.inline import keyboards_text
from src.client_openai import post_generator, whisper
from src.telegram.utils import escape_markdown_v2
from src.constants import *

router = Router()


@router.message(F.voice, Chat.send_message)
async def send_voice_text_to_openai(
    message: Message, uow: UnitOfWork, state: FSMContext, bot: Bot
):
    msg_to_delete = await message.answer("Распознаю голос...")

    file = await bot.get_file(message.voice.file_id)
    file_path = file.file_path
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
    local_path = TMP_DIR / f"{message.from_user.id}.ogg"

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open(local_path, "wb") as f:
                    f.write(await resp.read())

    transcription = await whisper.get_transcription(str(local_path))
    os.remove(local_path)

    if not transcription:
        await message.answer("Не удалось распознать голос 😔")
    else:
        await message.answer(
            text=transcription,
            reply_markup=create_vertical_keyboard(
                keyboards_text.chose_transcription_buttons
            ),
        )

        await state.update_data({"data": transcription})

    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )
