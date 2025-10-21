import os
import asyncio
import aiohttp

from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.database.uow import UnitOfWork
from src.telegram.states import GenerateSemantic
from src.telegram import texts
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.keyboards.inline import keyboards_text
from src.client_openai import semantic_layout_generator
from src.telegram.utils import escape_markdown_v2
from src.telegram.prompts import alcove_prompt
from src.constants import *


router = Router()


@router.callback_query(F.data == "assemble_posts_for_layout")
async def assemble_posts_for_layout(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.assemble_posts_for_layout_text,
        reply_markup=create_vertical_keyboard(keyboards_text.begin_breaf_buttons),
    )


@router.callback_query(F.data == "help")
async def assemble_posts_for_layout_help(call: CallbackQuery, uow: UnitOfWork):
    await call.message.answer(
        text=texts.assemble_posts_for_layout_help_text,
        reply_markup=create_vertical_keyboard(keyboards_text.begin_breaf_buttons),
    )


@router.callback_query(F.data == "breaf_begin")
async def breaf_begin(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.quastions_text,
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
    )
    await state.set_state(GenerateSemantic.forward_1)


@router.callback_query(F.data == "forward", GenerateSemantic.forward_1)
async def alcove(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.alcove_text,
    )
    await state.set_state(GenerateSemantic.alcove)


@router.message(GenerateSemantic.alcove)
async def confirmed_alcove(message: Message, uow: UnitOfWork, state: FSMContext):
    await state.update_data({"alcove": message.text})
    await call.message.answer(
        text=texts.confirmed_text,
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
    )
    await state.set_state(GenerateSemantic.forward_2)


@router.callback_query(F.data == "forward", GenerateSemantic.forward_2)
async def main_goal(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.main_goal_text,
    )
    await state.set_state(GenerateSemantic.confirmed_main_goal)


@router.message(F.text, GenerateSemantic.confirmed_main_goal)
async def confirmed_main_goal(message: Message, uow: UnitOfWork, state: FSMContext):
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await semantic_layout_generator.get_thread(user.thread_id)
        alcove_text = await state.get_data()
        await semantic_layout_generator.create_message(
            alcove_prompt(alcove_text.get("alcove"), message.text), user.thread_id
        )
        response = await semantic_layout_generator.run_assistant(thread)
        await state.update_data({"main_goal": response})
        without_md = escape_markdown_v2(response)

    await message.answer(
        text=texts.confirmed_main_goal_text(without_md),
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
    )
    await state.set_state(GenerateSemantic.forward_2)
