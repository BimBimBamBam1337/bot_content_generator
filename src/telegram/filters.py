from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message
from datetime import datetime, timedelta, timezone

from src.database.uow import UnitOfWork


class PromoCodeExpiredFilter(BaseFilter):
    async def __call__(self, message: Message, uow: UnitOfWork, bot: Bot) -> bool:
        async with uow:
            user = await uow.user_repo.get(message.from_user.id)

            if not user.used_promo_codes:  # type: ignore
                return False

            promo_code, used_date_str = next(iter(user.used_promo_codes.items()))  # type: ignore
            code = await uow.promo_code_repo.get(promo_code)
            used_date = datetime.fromisoformat(used_date_str)

            if used_date.tzinfo is None:
                used_date = used_date.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)

            if now - used_date > timedelta(days=code.access_days):

                return True
        await message.answer("Промокод истёк, попробуй найти новый")
        return False
