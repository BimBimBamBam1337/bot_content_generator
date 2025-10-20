import asyncio
import aiohttp

from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove
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


@router.message(Promo.got_code)
async def check_code(message: Message, uow: UnitOfWork, state: FSMContext):
    await state.clear()
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        promo = await uow.promo_code_repo.get(message.text)

        if not promo:
            await message.answer(
                text=texts.not_right_promocode_text,
                reply_markup=create_vertical_keyboard(keyboards_text.go_back_to_menu),
            )
            return

        if message.text in user.used_promo_codes:
            await message.answer("Ты уже использовал этот промокод")
            return

        await uow.user_repo.add_promo_code(user, message.text)

        await message.answer(
            text=texts.rigth_promocde_text,
            reply_markup=create_vertical_keyboard(
                keyboards_text.assemble_posts_buttons
            ),
        )


@router.message(Chat.send_message)
async def send_message_to_openai(
    message: Message, uow: UnitOfWork, state: FSMContext, bot: Bot
):
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await post_generator.get_thread(user.thread_id)
        msg_to_delete = await message.answer("Генерирую ответ...")
        if message.text:
            await post_generator.create_message(message.text, user.thread_id)
            response = await post_generator.run_assistant(thread)
            await state.update_data({"data": response})

            await message.answer(
                text=response,
                reply_markup=create_vertical_keyboard(
                    keyboards_text.chose_transcription_buttons
                ),
                parse_mode="MarkdownV2",
            )
        else:
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
            await post_generator.create_message(transcription, user.thread_id)
            response = await post_generator.run_assistant(thread)
            await state.update_data({"data": response})
            await message.answer(
                text=escape_markdown_v2(response),
                reply_markup=create_vertical_keyboard(
                    keyboards_text.chose_transcription_buttons
                ),
                parse_mode="MarkdownV2",
            )
            os.remove(local_path)

        await bot.delete_message(
            chat_id=message.chat.id, message_id=msg_to_delete.message_id
        )
