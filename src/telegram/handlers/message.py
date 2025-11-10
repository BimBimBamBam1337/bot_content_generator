import os
import asyncio
import aiohttp

from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.config import settings
from src.database.uow import UnitOfWork
from src.telegram.states import Promo, Chat, ConfirmResponse
from src.telegram import texts
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.keyboards.inline import keyboards_text
from src.client_openai import AssistantOpenAI
from src.telegram.utils import escape_markdown_v2, generate_response
from src.constants import *
from src.telegram import prompts


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

        code = await uow.user_repo.add_promo_code(user, message.text)
        if code:
            code = await uow.promo_code_repo.get(message.text)
            await uow.subscription_repo.create(
                message.from_user.id, trial=int(code.access_days)
            )
        await message.answer(
            text=texts.rigth_promocde_text,
            reply_markup=create_vertical_keyboard(
                keyboards_text.assemble_posts_buttons
            ),
        )


@router.message(F.text, Chat.send_message)
async def send_message_to_openai(
    message: Message,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    msg_to_delete = await message.answer("Генерирую ответ...")
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        if not user.thread_id:
            thread = await assistant.create_thread()
            await uow.user_repo.update_user(
                message.from_user.id,
                thread_id=thread.id,
                assistant_id=settings.post_generator,
            )

            await assistant.create_message(message.text, thread.id)
            response = await assistant.run_assistant(thread)
        else:
            response = await generate_response(user, message.text, assistant)
            await state.update_data({"data": response})

        await message.answer(
            text=escape_markdown_v2(response),
            reply_markup=create_vertical_keyboard(
                keyboards_text.chose_transcription_buttons
            ),
            parse_mode="MarkdownV2",
        )
    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )


@router.message(
    F.text,
    StateFilter(
        ConfirmResponse.reels,
        ConfirmResponse.threads,
        ConfirmResponse.instagram,
        ConfirmResponse.telegram,
    ),
)
async def change_post(
    message: Message,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    response = await state.get_data()
    text = response.get("data")
    msg_to_delete = await message.answer("Генерирую ответ...")

    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        await assistant.create_message(
            prompts.regenerate_text(
                text,
                message.text,
            ),
            user.thread_id,
        )
        response = await assistant.run_assistant(thread)
        await state.update_data({"data": response})

        await message.answer(
            text=escape_markdown_v2(response),
            reply_markup=create_vertical_keyboard(keyboards_text.confirm_post_buttons),
            parse_mode="MarkdownV2",
        )
    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )
