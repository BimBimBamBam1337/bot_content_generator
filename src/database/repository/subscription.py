from datetime import datetime, timedelta

from sqlalchemy import delete, select, update, func
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.models import Subscription, User


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int) -> Subscription:
        subscription = Subscription(user_id=user_id)
        self.session.add(subscription)
        await self.session.flush()
        return subscription

    async def delete(self, user_id: int) -> None:
        await self.session.execute(
            delete(Subscription).where(Subscription.user_id == user_id)
        )
        await self.session.flush()

    async def get(self, user_id: int) -> Subscription | None:
        subscription = await self.session.get(Subscription, user_id)
        return subscription

    async def get_all(self) -> list[Subscription] | None:
        result = await self.session.execute(select(Subscription))
        subscription = result.scalars().all()
        return list(subscription)

    async def update_subscription(self, user_id: int, **kwargs) -> None:
        await self.session.execute(
            update(Subscription).where(Subscription.user_id == user_id).values(**kwargs)
        )
        await self.session.flush()

    async def get_total_cost_today(self) -> float:
        today = datetime.now().date()
        result = await self.session.execute(
            select(func.sum(Subscription.cost)).where(
                Subscription.activated_at >= today
            )
        )
        return float(result.scalar()) if result.scalar() else 0.0

    async def get_total_cost_this_month(self) -> float:
        now = datetime.now()
        start_of_month = now.replace(day=1)

        # начало следующего месяца
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)

        result = await self.session.execute(
            select(func.sum(Subscription.cost)).where(
                Subscription.activated_at >= start_of_month,
                Subscription.activated_at < next_month,
            )
        )
        total = result.scalar()
        return float(total) if total else 0.0

    async def get_total_today(self) -> int:
        today = datetime.now().date()
        result = await self.session.execute(
            select(func.count()).where(Subscription.activated_at >= today)
        )
        count = result.scalar()
        return int(count) if count else 0

    async def get_total_this_month(self) -> int:
        now = datetime.now()
        first_day = now.replace(day=1).date()
        result = await self.session.execute(
            select(func.count()).where(Subscription.activated_at >= first_day)
        )
        count = result.scalar()
        return int(count) if count else 0

    async def get_total_cost_this_week(self) -> float:
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        result = await self.session.execute(
            select(func.sum(Subscription.cost)).where(
                Subscription.activated_at >= start_of_week,
                Subscription.activated_at < end_of_week,
            )
        )
        total = result.scalar()
        return float(total) if total else 0.0

    async def get_expiring_in_days(self, days: int) -> list[Subscription]:
        target_date = (datetime.now() + timedelta(days=days)).date()

        result = await self.session.execute(
            select(Subscription).where(
                func.date(Subscription.expires_at) == target_date
            )
        )
        subscriptions = result.scalars().all()
        return list(subscriptions)

    async def get_active_unique_count(self) -> int:
        now = datetime.now()
        result = await self.session.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(
                Subscription.expires_at > now
            )
        )
        count = result.scalar()
        return int(count) if count else 0

    async def get_users_without_or_expired_subscription(self) -> list[int]:
        now = datetime.now()

        active_users_subquery = (
            select(Subscription.user_id)
            .where(Subscription.expires_at > now, Subscription.is_active.is_(True))
            .distinct()
        )

        result = await self.session.execute(
            select(User.id).where(User.id.not_in(active_users_subquery))
        )

        users = result.scalars().all()
        return list(users)
