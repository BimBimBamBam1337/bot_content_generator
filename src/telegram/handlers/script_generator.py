import os
import asyncio

from loguru import logger
from aiogram import Router, Bot, F
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.client_openai import AssistantOpenAI
from src.config import settings
from src.database.uow import UnitOfWork
from src.telegram.states import GenerateSemantic
from src.telegram import texts
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.keyboards.inline import keyboards_text
from src.telegram.utils import escape_markdown_v2, generate_response
from src.telegram.states import Chat
from src.telegram import prompts

from src.constants import *


router = Router()


@router.callback_query(F.data == "assemble_posts_for_layout")
async def assemble_posts_for_layout(
    call: CallbackQuery, uow: UnitOfWork, assistant: AssistantOpenAI = None
):
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)

        # Если assistant не передан, создаем его
        if assistant is None:
            assistant = AssistantOpenAI(
                settings.openai_key, settings.semantic_layout_generator
            )

        if user.thread_id:
            await uow.user_repo.update_user(
                call.from_user.id, assistant_id=settings.semantic_layout_generator
            )
        else:
            thread = await assistant.create_thread()
            await uow.user_repo.update_user(
                call.from_user.id,
                thread_id=thread.id,
                assistant_id=settings.semantic_layout_generator,
            )

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
async def confirmed_main_goal(
    message: Message, uow: UnitOfWork, state: FSMContext, assistant: AssistantOpenAI
):
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        alcove_text = await state.get_data()
        await assistant.create_message(
            prompts.alcove_prompt(alcove_text.get("alcove"), message.text),
            user.thread_id,
        )
        response = await assistant.run_assistant(thread)
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
    await state.set_state(GenerateSemantic.forward_5)


@router.message(F.text, GenerateSemantic.forward_5)
async def confirmed_format(message: Message, uow: UnitOfWork, state: FSMContext):
    await message.answer(
        text=texts.confirmed_format_text,
        reply_markup=create_vertical_keyboard(keyboards_text.forward_buttnon),
    )
    await state.update_data({"confirmed_format": message.text})
    await state.set_state(GenerateSemantic.forward_6)


@router.callback_query(F.data == "forward", GenerateSemantic.forward_6)
async def content_text(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.content_text,
    )
    await state.set_state(GenerateSemantic.confirmed_format)


@router.message(GenerateSemantic.confirmed_format)
async def generate_brief(
    message: Message,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    msg_to_delete = await message.answer("Генерирую ответ...")
    state_data = await state.get_data()
    main_goal = state_data.get("main_goal")
    confirmed_semantic = state_data.get("confirmed_semantic")
    confirmed_format = state_data.get("confirmed_semantic")
    content = message.text
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        await assistant.create_message(
            prompts.short_brief_prompt(
                main_goal, confirmed_semantic, confirmed_format, content
            ),
            user.thread_id,
        )
        response = await assistant.run_assistant(thread)
        await state.update_data({"short_brief": response})

    await message.answer(
        text=escape_markdown_v2(texts.short_brief_text(response)),
        reply_markup=create_vertical_keyboard(
            keyboards_text.confirm_begin_brief_buttons
        ),
        parse_mode="MarkdownV2",
    )
    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )


@router.callback_query(F.data == "change_brief")
async def regenerate_brief(call: CallbackQuery, uow: UnitOfWork, state: FSMContext):
    await call.message.answer(
        text=texts.regenerate_brief_text,
        parse_mode="MarkdownV2",
    )
    await state.set_state(GenerateSemantic.regenerate_brief)


@router.message(GenerateSemantic.regenerate_brief)
async def changed_brief(
    message: Message,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    msg_to_delete = await message.answer("Генерирую ответ...")
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        change_brief = await state.get_data()
        await assistant.create_message(
            prompts.regenerate_response_prompt_with_comments(
                message.text, change_brief.get("short_brief")
            ),
            user.thread_id,
        )
        response = await assistant.run_assistant(thread)
        await state.update_data({"short_brief": response})

    await message.answer(
        text=escape_markdown_v2(response),
        reply_markup=create_vertical_keyboard(
            keyboards_text.confirm_begin_brief_buttons
        ),
        parse_mode="MarkdownV2",
    )
    await state.set_state(GenerateSemantic.regenerate_brief)
    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )


@router.callback_query(F.data == "all_right")
async def generate_semantic_lines(
    call: CallbackQuery,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    msg_to_delete = await call.message.answer("Генерирую ответ...")
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        await assistant.create_message(
            prompts.three_semantic_line_prompt,
            user.thread_id,
        )
        response = await assistant.run_assistant(thread)
        await state.update_data({"three_semantic_line_prompt": response})

    await call.message.answer(
        text=escape_markdown_v2(texts.semantic_text(response)),
        reply_markup=create_vertical_keyboard(
            keyboards_text.confirm_semantic_line_buttons
        ),
        parse_mode="MarkdownV2",
    )
    await bot.delete_message(
        chat_id=call.message.chat.id, message_id=msg_to_delete.message_id
    )


@router.callback_query(F.data == "change_form")
async def regenerate_semantic_lines(
    call: CallbackQuery, uow: UnitOfWork, state: FSMContext
):
    await call.message.answer(
        text=texts.regenerate_semantic_lines_text,
        parse_mode="MarkdownV2",
    )
    await state.set_state(GenerateSemantic.regenerate_semantic_lines)


@router.message(GenerateSemantic.regenerate_semantic_lines)
async def changed_semantic_lines(
    message: Message,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    msg_to_delete = await message.answer("Генерирую ответ...")
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        change_semantic_lines = await state.get_data()
        await assistant.create_message(
            prompts.regenerate_response_prompt_with_comments(
                message.text, change_semantic_lines.get("three_semantic_line_prompt")
            ),
            user.thread_id,
        )
        response = await assistant.run_assistant(thread)
        await state.update_data({"three_semantic_line_prompt": response})

    await message.answer(
        text=escape_markdown_v2(response),
        reply_markup=create_vertical_keyboard(
            keyboards_text.confirm_semantic_line_buttons
        ),
        parse_mode="MarkdownV2",
    )
    await state.set_state(GenerateSemantic.regenerate_brief)
    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )


@router.callback_query(F.data == "go_forward")
async def generate_layout(
    call: CallbackQuery,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    msg_to_delete = await call.message.answer("Генерирую ответ...")
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
    response = await generate_response(
        user,
        prompts.layout_prompt,
        assistant,
    )
    await state.update_data({"layout_prompt": response})

    await bot.delete_message(
        chat_id=call.message.chat.id, message_id=msg_to_delete.message_id
    )

    await call.message.answer(
        text=escape_markdown_v2(texts.short_brief_text(response)),
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_layout_buttons),
        parse_mode="MarkdownV2",
    )


@router.callback_query(F.data == "regenerate_grid")
async def regenerate_layout(
    call: CallbackQuery,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    await call.message.answer(text=texts.regenerate_layout_text)
    await state.set_state(GenerateSemantic.regenerate_layout)


@router.message(F.text, GenerateSemantic.regenerate_layout)
async def got_regenerate_layout(
    message: Message,
    uow: UnitOfWork,
    state: FSMContext,
    bot: Bot,
    assistant: AssistantOpenAI,
):
    msg_to_delete = await message.answer("Пересобираю раскладку...")
    layout = await state.get_data()
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
    response = await generate_response(
        user,
        prompts.regenerate_response_prompt(layout.get("layout_prompt"), message.text),
        assistant,
    )
    await state.update_data({"layout_prompt": response})
    await bot.delete_message(
        chat_id=message.chat.id, message_id=msg_to_delete.message_id
    )

    await message.answer(
        text=escape_markdown_v2(texts.short_brief_text(response)),
        reply_markup=create_vertical_keyboard(keyboards_text.confirm_layout_buttons),
        parse_mode="MarkdownV2",
    )


@router.callback_query(F.data == "confirm_layout")
async def confirm_layout(
    call: CallbackQuery, uow: UnitOfWork, state: FSMContext, assistant: AssistantOpenAI
):

    await call.message.answer(
        text=texts.final_semantic_layout_text,
    )
    await state.clear()
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
        if user.thread_id:
            await assistant.delete_thread(user.thread_id)
        thread = await assistant.create_thread()
        await uow.user_repo.update_user(call.from_user.id, thread_id=thread.id)
