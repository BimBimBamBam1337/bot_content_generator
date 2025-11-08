import asyncio
import random
from aiogram.filters import StateFilter
from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.client_openai import AssistantOpenAI
from src.payment_system import *
from src.config import settings
from src.database.uow import UnitOfWork
from src.telegram.states import Chat, Promo, SendResponse, ConfirmResponse
from src.telegram import texts
from src.telegram.keyboards.inline import keyboards_text
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.prompts import type_prompts
from src.telegram.utils import escape_markdown_v2, generate_response
from src.constants import *
from src.telegram import prompts

router = Router()


@router.callback_query(F.data.in_(["one_month:499", "one_year:4999"]))
async def process_payment(call: CallbackQuery, state: FSMContext, uow: UnitOfWork):
    price = int(call.data.split(":")[1])
    response = create_payment(call.from_user.id, price)
    await call.message.answer(
        text=f"Ссылка на оплату:\n{response.url}",
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_payment_buttons),
    )
