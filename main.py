import asyncio
from aiohttp import web
from loguru import logger
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import setup_application

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
    await bot.set_webhook(settings.SITE_URL + "/webhook")
    logger.info(f"Webhook set to {settings.SITE_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def create_app():
    app = web.Application()

    app.router.add_post("/webhook", handle_webhook)

    setup_robokassa_routes(app)

    dm = DependanciesMiddleware()
    dp.message.outer_middleware(dm)
    dp.callback_query.outer_middleware(dm)
    dp.include_routers(*routers)

    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host=settings.SITE_HOST, port=settings.SITE_PORT)
