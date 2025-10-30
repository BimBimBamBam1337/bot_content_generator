import re

from aiogram.types import CallbackQuery, TelegramObject

from src.database.models import User
from src.client_openai import AssistantOpenAI
from src.database.uow import UnitOfWork


def escape_markdown_v2(text: str) -> str:
    # Все спецсимволы MarkdownV2, включая точку
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


async def generate_response(user: User, text: str, assistant: AssistantOpenAI):
    thread = await assistant.get_thread(user.thread_id)
    await assistant.create_message(text, user.thread_id)
    response = await assistant.run_assistant(thread)

    return response
