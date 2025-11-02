import asyncio
from aiogram.webhook.aiohttp_server import setup_application
from aiohttp import web
from aiogram.types import BotCommand
from loguru import logger


from src.config import dp, bot, settings
from src.telegram.handlers import routers
from src.telegram.midlewares import DependanciesMiddleware
from src.constants import *


async def setup_bot_commands():
    bot_commands = [
        BotCommand(command="/help", description="Информация о боте"),
        BotCommand(command="/cancel", description="Отмена действия"),
        BotCommand(command="/pay", description="Оплата бота"),
        BotCommand(command="/promo", description="Активировать промо код"),
        BotCommand(
            command="/generate", description="Сгенерировать раскладку или поста"
        ),
    ]
    await bot.set_my_commands(bot_commands)


async def main():
    dm = DependanciesMiddleware()

    # await bot.set_webhook(settings.get_webhook_url)
    await setup_bot_commands()
    dp.message.outer_middleware(dm)
    dp.callback_query.outer_middleware(dm)
    dp.my_chat_member.outer_middleware(dm)
    dp.include_routers(*routers)
    await bot.delete_webhook(drop_pending_updates=False)
    logger.info(f"Bot started {await bot.get_me()}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
