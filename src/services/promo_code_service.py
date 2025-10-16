from src.database.uow import UnitOfWork
from src.database.models import PromoCode


class PromoCodeService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_code(self, code: str) -> PromoCode:
        async with self.uow as uow:
            return await uow.promo_code_repo.create(code)

    async def get_user_by_id(self, code: str) -> PromoCode | None:
        async with self.uow as uow:
            return await uow.promo_code_repo.get(code)

    async def delete_user(self, code: str):
        async with self.uow as uow:
            await uow.promo_code_repo.delete(code)

    async def get_all_users(self) -> list[PromoCode] | None:
        async with self.uow as uow:
            return await uow.promo_code_repo.get_all()
