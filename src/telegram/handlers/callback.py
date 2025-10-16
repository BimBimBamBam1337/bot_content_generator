import asyncio

from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.client_openai import client
from src.database.uow import UnitOfWork
from src.telegram.filters import PromoCodeExpiredFilter
from src.telegram.states import Chat, Promo
from src.telegram import texts
from src.telegram.keyboards.inline import keyboards_text
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
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
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )


@router.callback_query(F.data == "telegram")
async def telegram(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.telegram_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )


@router.callback_query(F.data == "instagram")
async def instagram(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.instagram_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )


@router.callback_query(F.data == "threads")
async def threads(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.threads_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )


@router.callback_query(F.data == "article")
async def article(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.article_text,
        reply_markup=create_vertical_keyboard(
            keyboards_text.chose_language_post_buttons
        ),
    )
