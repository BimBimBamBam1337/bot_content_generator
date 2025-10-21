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
from src.telegram.prompts import alcove_prompt, short_brief_prompt
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
    await message.answer(
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

    await message.answer(
        text=escape_markdown_v2(texts.confirmed_main_goal_text(response)),
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
        parse_mode="MarkdownV2",
    )
    await state.set_state(GenerateSemantic.forward_3)


@router.callback_query(F.data == "forward", GenerateSemantic.forward_3)
async def three_semantic_lines(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.three_semantic_lines_text,
    )
    await state.set_state(GenerateSemantic.confirmed_semantic)


@router.message(GenerateSemantic.confirmed_semantic)
async def confirmed_semantic(message: Message, uow: UnitOfWork, state: FSMContext):
    await state.update_data({"confirmed_semantic": message.text})
    await message.answer(
        text=texts.confirmed_semantic_text,
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
    )
    await state.set_state(GenerateSemantic.forward_4)


@router.callback_query(F.data == "forward", GenerateSemantic.forward_4)
async def format_text(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.format_text,
    )
    await state.set_state(GenerateSemantic.confirmed_format)


@router.message(F.text, GenerateSemantic.confirmed_format)
async def confirmed_format(message: Message, uow: UnitOfWork, state: FSMContext):
    await message.answer(
        text=texts.confirmed_format_text,
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
    )
    await state.update_data({"confirmed_format": message.text})
    await state.set_state(GenerateSemantic.forward_5)


@router.callback_query(F.data == "forward", GenerateSemantic.forward_5)
async def format_text(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.content_text,
    )
    await state.set_state(GenerateSemantic.)


@router.message(GenerateSemantic.)
async def generate_response(message: Message, uow: UnitOfWork, state: FSMContext):
    state_data = await state.get_data()
    main_goal = state_data.get("main_goal")
    confirmed_semantic = state_data.get("confirmed_semantic")
    confirmed_format = state_data.get("confirmed_semantic")
    content = message.text
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await semantic_layout_generator.get_thread(user.thread_id)
        await semantic_layout_generator.create_message(
            short_brief_prompt(main_goal, confirmed_semantic, confirmed_format, content),
            user.thread_id,
        )
        response = await semantic_layout_generator.run_assistant(thread)
        await state.update_data({"main_goal": response})

    await message.answer(
        text=escape_markdown_v2(texts.short_brief_text(response)),
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
        parse_mode="MarkdownV2",
    )
