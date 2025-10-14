from aiogram.filters import BaseFilter
from aiogram.types import Message


class AdminFilter(BaseFilter):
    def __init__(self):
        self.admin_id = [422297622, 8128765533, 1107806304]

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_id  # type: ignore
