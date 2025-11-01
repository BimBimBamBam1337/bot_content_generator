from datetime import datetime, timedelta

from sqlalchemy import delete, select, update, func
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.models import Subscription


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
        month_ago = datetime.now().date() - timedelta(days=30)
        result = await self.session.execute(
            select(func.sum(Subscription.cost)).where(
                Subscription.activated_at >= month_ago
            )
        )
        return float(result.scalar()) if result.scalar() else 0.0
