from datetime import datetime, timedelta

from sqlalchemy import delete, select, update, func
from sqlalchemy.ext.asyncio.session import AsyncSession


from src.database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int) -> User:
        user = User(id=user_id)
        self.session.add(user)
        await self.session.flush()
        return user

    async def delete(self, user_id: int) -> None:
        await self.session.execute(delete(User).where(User.id == user_id))
        await self.session.flush()

    async def add_promo_code(self, user: User, promo_code: str) -> bool:
        if promo_code in user.used_promo_codes:
            return False

        user.used_promo_codes[promo_code] = datetime.now().isoformat()

        self.session.add(user)
        await self.session.flush()
        return True

    async def get(self, user_id: int) -> User | None:
        user = await self.session.get(User, user_id)
        return user

    async def get_all(self) -> list[User] | None:
        result = await self.session.execute(select(User))
        users = result.scalars().all()
        return list(users)

    async def update_user(self, user_id: int, **kwargs) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await self.session.flush()

    async def get_total_by_days(self, days: int = None) -> list[User]:
        if days is None:
            total = await self.session.scalars(select(User))
        else:
            now = datetime.now()
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=days)

            total = await self.session.scalars(
                select(User).where(
                    User.created_at >= start_of_week,
                    User.created_at < end_of_week,
                )
            )

        return list(total.all())
