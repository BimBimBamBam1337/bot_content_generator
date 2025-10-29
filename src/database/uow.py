from sqlalchemy.ext.asyncio import AsyncSession
from .repository import *


class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session: AsyncSession = self.session_factory()
        self.user_repo: UserRepository = UserRepository(self.session)
        self.promo_code_repo: PromoCodeRepository = PromoCodeRepository(self.session)
        return self

    # async def __aexit__(
    #     self,
    #     exc_type: type[BaseException] | None,
    #     exc_val: BaseException | None,
    #     exc_tb: object | None,
    # ) -> None:
    #     if exc_type is not None:
    #         await self.rollback()
    #     else:
    #         await self.commit()
    #     await self.session.close()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
