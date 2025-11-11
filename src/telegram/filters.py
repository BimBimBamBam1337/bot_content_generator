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

            # Приводим expires_at к UTC для корректного сравнения
            if subscription.expires_at.tzinfo is None:
                # Если expires_at наивный (без временной зоны), считаем что он в UTC
                expires_at_utc = subscription.expires_at.replace(tzinfo=timezone.utc)
            else:
                # Если уже имеет временную зону, конвертируем в UTC
                expires_at_utc = subscription.expires_at.astimezone(timezone.utc)

            if now > expires_at_utc:
                await message.answer("Твоя подписка истекла, попробуй найти новую")
                await state.clear()
                return False

        return True
