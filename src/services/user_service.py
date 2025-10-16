from datetime import datetime

from src.database.uow import UnitOfWork
from src.database.models import User


class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_user(self, user_id: int, thread_id: str) -> User:
        async with self.uow as uow:
            return await uow.user_repo.create(user_id, thread_id)

    async def get_user_by_id(self, user_id: int) -> User | None:
        async with self.uow as uow:
            return await uow.user_repo.get(user_id)

    async def add_promo_code(self, user: User, promo_code: str):
        async with self.uow as uow:
            return await uow.user_repo.add_promo_code(user, promo_code)

    async def delete_user(self, user_id: int):
        async with self.uow as uow:
            await uow.user_repo.delete(user_id)

    async def get_all_users(self) -> list[User] | None:
        async with self.uow as uow:
            return await uow.user_repo.get_all()
