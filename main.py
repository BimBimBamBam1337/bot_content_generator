import asyncio

from aiogram.types import FSInputFile
from loguru import logger

from src.config import dp, bot
from src.telegram.handlers import routers
from src.telegram.midlewares import DependanciesMiddleware
from src.constants import *


async def main():
    dm = DependanciesMiddleware()
    dp.message.outer_middleware(dm)
    dp.callback_query.outer_middleware(dm)
    dp.my_chat_member.outer_middleware(dm)
    dp.include_routers(*routers)
    await bot.delete_webhook(drop_pending_updates=False)
    logger.info(f"Bot started {await bot.get_me()}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
