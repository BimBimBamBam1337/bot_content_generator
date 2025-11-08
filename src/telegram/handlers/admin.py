import asyncio

from loguru import logger
from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.database.uow import UnitOfWork
from src.telegram.filters import AdminFilter
from src.telegram.states import CreatePromoCode
from src.telegram.keyboards.inline import keyboards_text
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram import texts

from src.constants import *


router = Router()


@router.callback_query(F.data == "users")
async def users(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.users_info_text,
        reply_markup=create_vertical_keyboard(keyboards_text.users_info_buttons),
    )


@router.callback_query(F.data == "payments")
async def payments(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.pay_text,
        reply_markup=create_vertical_keyboard(keyboards_text.how_much_buttons),
    )


@router.callback_query(F.data == "add_promo_code")
async def add_promo_code(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.add_promocode_name_text,
    )
    await state.set_state(CreatePromoCode.name)


@router.message(CreatePromoCode.name)
async def name_promo_code(message: Message, uow: UnitOfWork, state: FSMContext):
    async with uow:
        promo_code = await uow.promo_code_repo.get(message.text)
        if promo_code:
            await message.answer(text="Промокод уже существует")
            return
    await message.answer(
        text=texts.add_promocode_days_text,
    )
    await state.update_data({"name": message.text})
    await state.set_state(CreatePromoCode.days)


@router.message(CreatePromoCode.days)
async def give_days_promo_code(message: Message, uow: UnitOfWork, state: FSMContext):
    data = await state.get_data()
    try:
        async with uow:
            promo_code = await uow.promo_code_repo.create(
                data.get("name"), int(message.text)
            )
            if promo_code:
                await message.answer(
                    text=texts.add_promocode_seccesfull_text(promo_code.code),
                    reply_markup=create_vertical_keyboard(
                        keyboards_text.how_much_buttons
                    ),
                )
        await state.clear()
    except Exception:
        await message.answer(text="Это должно быть число")
