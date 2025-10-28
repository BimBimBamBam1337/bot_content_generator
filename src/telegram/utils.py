import re

from aiogram.types import CallbackQuery

from src.client_openai import AssistantOpenAI
from src.database.uow import UnitOfWork


def escape_markdown_v2(text: str) -> str:
    # Спецсимволы MarkdownV2, которые ломают Telegram
    # но ** и _ оставляем, чтобы жирный и курсив работали
    # список безопасных для экранирования: ! . ( ) [ ] ~ > # + - = | { }
    return re.sub(r"([!.\[\]()~>#+\-=|{}])", r"\\\1", text)


async def generate_semantic_layout_generator(
    uow: UnitOfWork, call: CallbackQuery, text: str, assistant: AssistantOpenAI
):
    async with uow:
        user = await uow.user_repo.get(call.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        await assistant.create_message(text, user.thread_id)
        response = await assistant.run_assistant(thread)

    return response
