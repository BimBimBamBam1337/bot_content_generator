import asyncio

from aiogram.filters import StateFilter
from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from langdetect import detect

from src.client_openai import post_generator
from src.database.uow import UnitOfWork
from src.telegram.filters import PromoCodeExpiredFilter
from src.telegram.states import Chat, Promo, SendResponse
from src.telegram import texts
from src.telegram.keyboards.inline import keyboards_text
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.prompts import language_map, type_prompts
from src.telegram.utils import escape_markdown_v2
from src.constants import *

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


@router.callback_query(F.data == "assemble_posts", PromoCodeExpiredFilter())
async def assemble_posts(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
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
    await call.message.answer(
        text=texts.telegram_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )
    await state.set_state(SendResponse.telegram)


@router.callback_query(F.data == "instagram")
async def instagram(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.instagram_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )
    await state.set_state(SendResponse.instagram)


@router.callback_query(F.data == "threads")
async def threads(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.threads_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )
    await state.set_state(SendResponse.threads)


@router.callback_query(F.data == "article")
async def article(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.article_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )
    await state.set_state(SendResponse.article)


@router.callback_query(SendResponse.prepare_reels)
async def prepare_reels(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await state.update_data(call_data=call.data)

    await call.message.answer(
        text=texts.reels_language_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )
    await state.set_state(SendResponse.reels)


@router.callback_query(SendResponse.reels)
async def generate_reels(
    message: Message, call: CallbackQuery, uow: UnitOfWork, state: FSMContext, bot: Bot
):
    response = await state.get_data()
    state_data = response.get("call_data")
    text = response.get("data")
    chosen_language = call.data

    base_prompt = type_prompts.get(state_data, "Создай контент")
    language_text = language_map.get(chosen_language, "на языке исходного текста")
    message_text = f"{base_prompt} {language_text} на основе следующего текста: {text}"
    msg_to_delete = await message.answer("Генерирую ответ...")
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
        thread = await post_generator.get_thread(user.thread_id)
        await post_generator.create_message(message_text, user.thread_id)
        response_text = await post_generator.run_assistant(thread)

    await call.message.answer(
        text=escape_markdown_v2(response_text), parse_mode="MarkdownV2"
    )
    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )


@router.callback_query(
    StateFilter(
        SendResponse.article,
        SendResponse.reels,
        SendResponse.threads,
        SendResponse.instagram,
        SendResponse.telegram,
    ),
)
async def chose_language_auto(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    response = await state.get_data()
    main_state = await state.get_state()
    post_type = main_state.split(":")[1]
    text = response.get("data")

    try:
        detected_lang = detect(text)
    except Exception:
        detected_lang = "en"

    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
        thread = await post_generator.get_thread(user.thread_id)

        if detected_lang == "ru":
            message_text = f"Создай {post_type} на русском языке на основе следующего текста: {text}"
        else:
            message_text = (
                f"Create a {post_type} in English based on the following text: {text}"
            )

        await post_generator.create_message(message_text, user.thread_id)
        response_text = await post_generator.run_assistant(thread)

    await call.message.answer(
        text=escape_markdown_v2(response_text), parse_mode="MarkdownV2"
    )
