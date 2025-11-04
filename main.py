import asyncio
from aiohttp import web
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import setup_application
from loguru import logger

from src.config import dp, bot, settings
from src.telegram.midlewares import DependanciesMiddleware
from src.telegram.handlers import routers
from src.telegram.webhook import handle_webhook, setup_robokassa_routes


async def setup_bot_commands():
    await bot.set_my_commands(
        [
            BotCommand(command="/help", description="Информация о боте"),
            BotCommand(command="/cancel", description="Отмена действия"),
            BotCommand(command="/pay", description="Оплата бота"),
            BotCommand(command="/promo", description="Активировать промокод"),
            BotCommand(command="/generate", description="Сгенерировать пост"),
        ]
    )


async def on_startup(app):
    await setup_bot_commands()
    await bot.set_webhook(settings.get_webhook_url)
    logger.info(f"Webhook set to {settings.get_webhook_url}")
    logger.info(f"Bot started as {await bot.get_me()}")


async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def create_app():
    app = web.Application()

    # Telegram webhook
    app.router.add_post("/webhook", handle_webhook)

    # Robokassa маршруты
    setup_robokassa_routes(app)

    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


async def main():
    dm = DependanciesMiddleware()
    await setup_bot_commands()
    dp.message.outer_middleware(dm)
    dp.callback_query.outer_middleware(dm)
    dp.include_routers(*routers)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)
    logger.info(f"Bot started as {await bot.get_me()}")


if __name__ == "__main__":
    asyncio.run(main())
