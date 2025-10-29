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
from src.telegram.states import Chat, Promo, SendResponse
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


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery, uow: UnitOfWork):
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
            thread_id = await assistant.create_thread()
            await uow.user_repo.update_user(call.from_user.id, thread_id=thread_id)
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
    await state.set_state(SendResponse.prepare_reels)


@router.callback_query(F.data == "telegram")
async def telegram(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    state_data = await state.get_data()
    await call.message.answer(
        text=texts.type_post(state_data.get("data"), call.data),
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_post_buttons),
    )
    await state.set_state(SendResponse.telegram)


@router.callback_query(F.data == "instagram")
async def instagram(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    state_data = await state.get_data()
    await call.message.answer(
        text=texts.type_post(state_data.get("data"), call.data),
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_post_buttons),
    )
    await state.set_state(SendResponse.instagram)


@router.callback_query(F.data == "threads")
async def threads(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    state_data = await state.get_data()
    await call.message.answer(
        text=texts.type_post(state_data.get("data"), call.data),
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_post_buttons),
    )
    await state.set_state(SendResponse.threads)


@router.callback_query(SendResponse.reels)
async def generate_reels(
    call: CallbackQuery, uow: UnitOfWork, state: FSMContext, bot: Bot
):
    response = await state.get_data()
    state_data = response.get("call_data")
    text = response.get("data")

    base_prompt = type_prompts.get(state_data, "Создай контент")
    message_text = f"{base_prompt} основе следующего текста: {text}"
    msg_to_delete = await call.message.answer("Генерирую ответ...")
    response = await generate_response(
        uow, call, prompts.prompt_text(message_text, text), post_generator
    )
    await state.update_data({"response": response})
    await call.message.answer(
        text=escape_markdown_v2(response), parse_mode="MarkdownV2"
    )
    await bot.delete_message(
        chat_id=call.message.chat.id, message_id=msg_to_delete.message_id
    )


@router.callback_query(
    StateFilter(
        SendResponse.reels,
        SendResponse.threads,
        SendResponse.instagram,
        SendResponse.telegram,
    ),
)
async def generate_post(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    response = await state.get_data()
    main_state = await state.get_state()
    post_type = main_state.split(":")[1]
    text = response.get("data")
    response = await generate_response(
        uow, call, prompts.prompt_text(post_type, text), post_generator
    )
    await state.update_data({"response": response})
    await call.message.answer(
        text=escape_markdown_v2(texts.type_post(main_state.get("response"), post_type)),
        parse_mode="MarkdownV2",
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_post_buttons),
    )


@router.callback_query(
    F.data == "confirm",
    StateFilter(
        SendResponse.reels,
        SendResponse.threads,
        SendResponse.instagram,
        SendResponse.telegram,
    ),
)
async def confirm_post(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    main_state = await state.get_state()
    if main_state.split(":")[1] == "reels":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.reels_buttons),
            parse_mode="MarkdownV2",
        )
    if main_state.split(":")[1] == "telegram":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.telegram_buttons),
            parse_mode="MarkdownV2",
        )
    if main_state.split(":")[1] == "instagram":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.instagram_buttons),
            parse_mode="MarkdownV2",
        )
    if main_state.split(":")[1] == "threads":
        await call.message.answer(
            text=texts.confirmed_post_text,
            reply_markup=create_vertical_keyboard(keyboards_text.thread_buttons),
            parse_mode="MarkdownV2",
        )


@router.callback_query(
    F.data == "change",
    StateFilter(
        SendResponse.reels,
        SendResponse.threads,
        SendResponse.instagram,
        SendResponse.telegram,
    ),
)
async def change_post(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    main_state = await state.get_state()
    await call.message.answer(
        text=texts.what_to_change_text,
        parse_mode="MarkdownV2",
    )
