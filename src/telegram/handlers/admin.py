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


@router.callback_query(F.data == "bact_to_admin", AdminFilter())
async def admin(call: CallbackQuery, uow: UnitOfWork):
    """Команда для оплаты"""
    async with uow:
        all_users = await uow.user_repo.get_all()
        users_subscribed = await uow.subscription_repo.get_total_today()
        summ_subscribed = await uow.subscription_repo.get_total_cost_this_month()
    await call.message.answer(
        text=texts.statistic_text(len(all_users), users_subscribed, summ_subscribed),
        reply_markup=create_vertical_keyboard(keyboards_text.admin_buttons),
    )


@router.callback_query(F.data == "with_subscrioption")
async def with_subscrioption(call: CallbackQuery, uow: UnitOfWork):
    async with uow:
        subcribed = await uow.subscription_repo.get_active_unique()
        sum = await uow.subscription_repo.get_total_cost_this_month()
    await call.message.answer(
        text=texts.with_subscription(len(subcribed), sum),
        reply_markup=create_vertical_keyboard(keyboards_text.statistic_buttons),
    )


@router.callback_query(F.data == "without_subscrioption")
async def without_subscrioption(call: CallbackQuery, uow: UnitOfWork):
    async with uow:
        not_subcribed = await uow.subscription_repo.get_users_without_any_subscription()
    await call.message.answer(
        text=texts.without_subscription(len(not_subcribed)),
        reply_markup=create_vertical_keyboard(keyboards_text.statistic_buttons),
    )


@router.callback_query(F.data == "excpires_3_days")
async def excpires_3_days(call: CallbackQuery, uow: UnitOfWork):
    async with uow:
        subscription_excpires_3_days = await uow.subscription_repo.get_expiring_in_days(
            3
        )
    await call.message.answer(
        text=texts.excpires_3_days(len(subscription_excpires_3_days)),
        reply_markup=create_vertical_keyboard(keyboards_text.statistic_buttons),
    )


@router.callback_query(F.data == "new_for_week")
async def new_for_week(call: CallbackQuery, uow: UnitOfWork):
    async with uow:
        new_users = await uow.user_repo.get_total_by_days()
        new_subcribes = await uow.subscription_repo.get_active_unique(days=7)
        sum = await uow.subscription_repo.get_total_cost_this_month()

    await call.message.answer(
        text=texts.new_for_week(len(new_users), len(new_subcribes), sum),
        reply_markup=create_vertical_keyboard(keyboards_text.statistic_buttons),
    )


@router.callback_query(F.data.in_(["users", "back_to_users"]))
async def users(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.users_info_text,
        reply_markup=create_vertical_keyboard(keyboards_text.users_info_buttons),
    )


@router.callback_query(F.data == "payments")
async def payments(call: CallbackQuery, uow: UnitOfWork):
    async with uow:
        users_subscribed_summ_today = await uow.subscription_repo.get_total_cost_today()
        users_subscribed_today = await uow.subscription_repo.get_total_today()
        users_subscribed_this_month = await uow.subscription_repo.get_total_this_month()
        users_subscribed_summ_this_month = (
            await uow.subscription_repo.get_total_cost_this_month()
        )

    await call.message.answer(
        text=texts.finance_statistic_text(
            users_subscribed_today,
            users_subscribed_summ_today,
            users_subscribed_this_month,
            users_subscribed_summ_this_month,
        ),
        reply_markup=create_vertical_keyboard(keyboards_text.bact_to_admin_buttons),
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
                )
        await state.clear()
    except Exception:
        await message.answer(text="Это должно быть число")
