import re

from aiogram.types import CallbackQuery, TelegramObject

from src.client_openai import AssistantOpenAI
from src.database.uow import UnitOfWork

def escape_markdown_v2(text: str) -> str:
    # сначала экранируем только безопасные символы, кроме тех, что используются в форматировании
    escaped = re.sub(r'([!()\[\]~>#+\-=|{}])', r'\\\1', text)

    # экранируем точки, только если они не внутри URL
    escaped = re.sub(r'(?<!https?):(?<!\w)\.', r'\\.', escaped)
    return escaped


async def generate_response(
    uow: UnitOfWork, event: TelegramObject, text: str, assistant: AssistantOpenAI
):
    async with uow:
        user = await uow.user_repo.get(event.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        await assistant.create_message(text, user.thread_id)
        response = await assistant.run_assistant(thread)

    return response
