from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.database.models import PromoCode


class PromoCodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, promo_code: str) -> PromoCode:
        promo_code = PromoCode(code=promo_code)
        self.session.add(promo_code)
        await self.session.flush()
        return promo_code

    async def delete(self, promo_code: str) -> None:
        await self.session.execute(
            delete(PromoCode).where(PromoCode.code == promo_code)
        )
        await self.session.flush()

    async def get(self, promo_code: str | None) -> PromoCode | None:
        result = await self.session.execute(
            select(PromoCode).where(PromoCode.code == promo_code)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[PromoCode] | None:
        result = await self.session.execute(select(PromoCode))
        promo_codes = result.scalars().all()
        return list(promo_codes)
