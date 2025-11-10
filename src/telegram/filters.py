from re import L
from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message, TelegramObject
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone

from src.database.uow import UnitOfWork


class AdminFilter(BaseFilter):
    async def __call__(self, event: TelegramObject, uow: UnitOfWork) -> bool:
        async with uow:
            user = await uow.user_repo.get(event.from_user.id)
            if user.is_admin:
                return True
            return False


class SubscriptionExpiredFilter(BaseFilter):
    async def __call__(
        self, message: Message, uow: UnitOfWork, bot: Bot, state: FSMContext
    ) -> bool:
        async with uow:
            # Получаем подписку пользователя
            subscription = await uow.subscription_repo.get_active_by_user_id(
                message.from_user.id
            )

            if not subscription:
                await message.answer("У тебя нет активной подписки")
                await state.clear()
                return False

            now = datetime.now(timezone.utc)

            # Create a timezone-aware copy for comparison without modifying the original
            expires_at_aware = subscription.expires_at
            if expires_at_aware.tzinfo is None:
                expires_at_aware = expires_at_aware.replace(tzinfo=timezone.utc)

            if now > expires_at_aware:
                await message.answer("Твоя подписка истекла, попробуй найти новую")
                await state.clear()
                return False

        return True
