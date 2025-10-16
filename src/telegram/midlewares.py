from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timedelta

from aiogram.types import TelegramObject, FSInputFile
from aiogram import BaseMiddleware
from loguru import logger
from src.database.uow import UnitOfWork
from src.database.engine import SessionFactory


class DependanciesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["uow"] = UnitOfWork(SessionFactory)
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"An error ocured: {e}")
