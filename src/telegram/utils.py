import re

from aiogram.types import CallbackQuery, TelegramObject

from src.client_openai import AssistantOpenAI
from src.database.uow import UnitOfWork


def escape_markdown_v2(text: str) -> str:
    """
    Экранирует спецсимволы MarkdownV2, кроме ** и _,
    чтобы Telegram не кидал ошибку "can't parse entities".
    """
    # Символы, требующие экранирования по спецификации Telegram MarkdownV2
    # https://core.telegram.org/bots/api#markdownv2-style
    pattern = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(pattern, r'\\\1', text)


async def generate_response(
    uow: UnitOfWork, event: TelegramObject, text: str, assistant: AssistantOpenAI
):
    async with uow:
        user = await uow.user_repo.get(event.from_user.id)
        thread = await assistant.get_thread(user.thread_id)
        await assistant.create_message(text, user.thread_id)
        response = await assistant.run_assistant(thread)

    return response
