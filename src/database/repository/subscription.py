from datetime import datetime, timedelta

from sqlalchemy import delete, select, update, func, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.models import Subscription, User


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: int, cost: int = 0, promo_code_id=None, trial: int = 0
    ) -> Subscription:
        expires_at = datetime.now() + timedelta(trial)
        subscription = Subscription(
            user_id=user_id,
            cost=cost,
            promo_code_id=promo_code_id,
            expires_at=expires_at,
        )
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

    async def get_active_by_user_id(self, user_id: int) -> Subscription:
        subscription = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.is_active == True)
            .order_by(Subscription.activated_at.desc())
            .limit(1)
        )
        return subscription.scalar_one_or_none()

    async def get_total_cost_today(self) -> float:
        today = datetime.now().date()
        total = await self.session.scalar(
            select(func.sum(Subscription.cost)).where(
                Subscription.activated_at >= today
            )
        )
        return float(total) if total else 0.0

    async def get_total_cost_this_month(self) -> float:
        now = datetime.now()
        start_of_month = now.replace(day=1)
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)

        total = await self.session.scalar(
            select(func.sum(Subscription.cost)).where(
                Subscription.activated_at >= start_of_month,
                Subscription.activated_at < next_month,
            )
        )
        return float(total) if total else 0.0

    async def get_total_today(self) -> int:
        today = datetime.now().date()
        count = await self.session.scalar(
            select(func.count()).where(Subscription.activated_at >= today)
        )
        return int(count) if count else 0

    async def get_total_this_month(self) -> int:
        now = datetime.now()
        first_day = now.replace(day=1).date()
        count = await self.session.scalar(
            select(func.count()).where(Subscription.activated_at >= first_day)
        )
        return int(count) if count else 0

    async def get_total_cost_this_week(self) -> float:
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        total = await self.session.scalar(
            select(func.sum(Subscription.cost)).where(
                Subscription.activated_at >= start_of_week,
                Subscription.activated_at < end_of_week,
            )
        )
        return float(total) if total else 0.0

    async def get_expiring_in_days(self, days: int) -> list[Subscription]:
        target_date = (datetime.now() + timedelta(days=days)).date()
        subscriptions = await self.session.scalars(
            select(Subscription).where(
                func.date(Subscription.expires_at) == target_date
            )
        )
        return list(subscriptions)

    # async def get_active_unique(self, days: int | None = None) -> list[Subscription]:
    #     now = datetime.now()
    #     query = (
    #         select(Subscription)
    #         .options(joinedload(Subscription.user))
    #         .order_by(Subscription.user_id, Subscription.activated_at.desc())
    #     )
    #
    #     if days is not None:
    #         start_date = now - timedelta(days=days)
    #         query = query.where(
    #             and_(
    #                 Subscription.activated_at >= start_date,
    #                 Subscription.activated_at <= now,
    #             )
    #         )
    #     else:
    #         query = query.where(Subscription.expires_at > now)
    #
    #     result = await self.session.scalars(query)
    #     subscriptions = list(result.all())
    #
    #     # оставить только последние подписки для каждого пользователя
    #     unique_subs = {}
    #     for sub in subscriptions:
    #         if sub.user_id not in unique_subs:
    #             unique_subs[sub.user_id] = sub
    #
    #     return list(unique_subs.values())

    async def get_active_unique(self, days: int = None) -> list[Subscription]:

        now = datetime.now()
        query = select(Subscription)

        if days is not None:
            start_date = now - timedelta(days=days)
            query = query.where(
                and_(
                    Subscription.activated_at <= now,
                    Subscription.expires_at >= start_date,
                )
            )
        else:
            query = query.where(Subscription.expires_at > now)

        result = await self.session.scalars(query)
        subscriptions = list(result.all())
        return subscriptions

    async def get_users_without_or_expired_subscription(self) -> list[int]:
        now = datetime.now()
        active_users_subquery = (
            select(Subscription.user_id)
            .where(Subscription.expires_at > now, Subscription.is_active.is_(True))
            .distinct()
        )

        users = await self.session.scalars(
            select(User.id).where(User.id.not_in(active_users_subquery))
        )
        return list(users)

    async def get_total_cost_by_user_id(self, user_id: int) -> float:

        total = await self.session.scalar(
            select(func.sum(Subscription.cost)).where(
                Subscription.user_id == user_id,
            )
        )
        return float(total) if total else 0.0

    async def get_total_cost(self) -> float:

        total = await self.session.scalar(select(func.sum(Subscription.cost)))
        return float(total) if total else 0.0

    async def get_list_actvated_at(self, user_id: int) -> list[datetime]:

        total = await self.session.scalars(
            select(Subscription.activated_at).where(
                Subscription.user_id == user_id,
            )
        )
        return list(total.all())

    async def get_users_without_any_subscription(self) -> list[User]:
        query = (
            select(User)
            .outerjoin(Subscription, User.id == Subscription.user_id)
            .where(Subscription.id.is_(None))
        )

        result = await self.session.scalars(query)
        users = list(result.unique().all())
        return users
