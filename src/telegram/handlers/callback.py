import asyncio

from aiogram.filters import StateFilter
from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.client_openai import AssistantOpenAI
from src.config import settings
from src.database.uow import UnitOfWork
from src.telegram.filters import PromoCodeExpiredFilter
from src.telegram.states import Chat, Promo, SendResponse, ConfirmResponse
from src.telegram import texts
from src.telegram.keyboards.inline import keyboards_text
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.prompts import type_prompts
from src.telegram.utils import escape_markdown_v2, generate_response
from src.constants import *
from src.telegram import prompts

router = Router()


@router.callback_query(F.data == "subscribe")
async def subscribe(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.pay_text,
        reply_markup=create_vertical_keyboard(keyboards_text.how_much_buttons),
    )


@router.callback_query(F.data == "activate_promocode")
async def promo(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.promo_text,
    )
    await state.set_state(Promo.got_code)


@router.callback_query(F.data == "back_to_start")
async def back_to_start(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.start_text,
        reply_markup=create_vertical_keyboard(keyboards_text.subscription_menu_buttons),
    )


@router.callback_query(F.data.in_(["main_menu", "final_confirm"]))
async def back_to_menu(
    call: CallbackQuery, uow: UnitOfWork, assistant: AssistantOpenAI
):
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
        if user.thread_id:
            await assistant.delete_thread(user.thread_id)
            thread = await assistant.create_thread()
            await uow.user_repo.update_user(call.from_user.id, thread_id=thread.id)
    await call.message.answer(
        text=texts.generate_command_text,
        reply_markup=create_vertical_keyboard(keyboards_text.assemble_posts_buttons),
    )


@router.callback_query(F.data == "assemble_posts", PromoCodeExpiredFilter())
async def assemble_posts(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
        if user:
            await uow.user_repo.update_user(
                call.from_user.id, assistant_id=settings.post_generator
            )
    await call.message.answer(
        text=texts.send_text_or_voice_text,
    )
    await state.set_state(Chat.send_message)


@router.callback_query(F.data == "reels")
async def reels(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.reels_text,
        reply_markup=create_vertical_keyboard(keyboards_text.chose_script_buttos),
    )
    await state.set_state(SendResponse.reels)


@router.callback_query(SendResponse.reels)
async def generate_reels(
    call: CallbackQuery,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    response = await state.get_data()
    state_data = response.get("call_data")
    text = response.get("data")

    base_prompt = type_prompts.get(state_data, "Создай контент")
    message_text = f"{base_prompt} основе следующего текста: {text}"
    msg_to_delete = await call.message.answer("Генерирую ответ...")
    response = await generate_response(
        uow,
        call,
        prompts.prompt_text(message_text, text),
        assistant,
    )
    await state.update_data({"response": response})
    await call.message.answer(
        text=escape_markdown_v2(response),
        parse_mode="MarkdownV2",
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_post_buttons),
    )
    await state.set_state(ConfirmResponse.reels)
    await bot.delete_message(
        chat_id=call.message.chat.id, message_id=msg_to_delete.message_id
    )


@router.callback_query(F.data.in_(["instagram", "telegram", "threads"]))
async def generate_post(
    call: CallbackQuery, uow: UnitOfWork, state: FSMContext, assistant: AssistantOpenAI
):
    response = await state.get_data()
    text = response.get("data")
    response = await generate_response(
        uow, call, prompts.prompt_text(call.data, text), assistant
    )
    await state.update_data({"response": response})
    await call.message.answer(
        text=escape_markdown_v2(texts.type_post(response, call.data)),
        parse_mode="MarkdownV2",
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_post_buttons),
    )
    if call.data == "telegram":
        await state.set_state(ConfirmResponse.telegram)
    if call.data == "instagram":
        await state.set_state(ConfirmResponse.instagram)
    if call.data == "threads":
        await state.set_state(ConfirmResponse.threads)


@router.callback_query(
    F.data == "confirm",
    StateFilter(
        ConfirmResponse.reels,
        ConfirmResponse.threads,
        ConfirmResponse.instagram,
        ConfirmResponse.telegram,
    ),
)
async def confirm_post(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    main_state = await state.get_state()
    if main_state.split(":")[1] == "reels":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.reels_buttons),
        )
    if main_state.split(":")[1] == "telegram":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.telegram_buttons),
        )
    if main_state.split(":")[1] == "instagram":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.instagram_buttons),
        )
    if main_state.split(":")[1] == "threads":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.thread_buttons),
        )


@router.callback_query(
    F.data == "change",
    StateFilter(
        ConfirmResponse.reels,
        ConfirmResponse.threads,
        ConfirmResponse.instagram,
        ConfirmResponse.telegram,
    ),
)
async def change_post(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    main_state = await state.get_state()
    await call.message.answer(
        text=texts.what_to_change_text,
        parse_mode="MarkdownV2",
    )
