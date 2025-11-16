from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timedelta

from aiogram.types import TelegramObject, FSInputFile
from aiogram import BaseMiddleware
from loguru import logger

from src.client_openai import AssistantOpenAI
from src.config import settings
from src.database.uow import UnitOfWork
from src.database.engine import SessionFactory


class DependanciesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        uow = UnitOfWork(SessionFactory)
        data["uow"] = uow
        async with uow:
            user = await uow.user_repo.get(event.from_user.id)
            if user and user.assistant_id:
                data["assistant"] = AssistantOpenAI(
                    settings.openai_key, user.assistant_id
                )
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error("An error ocured: {}", e)
