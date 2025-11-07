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


async def on_startup(app: web.Application):
    await setup_bot_commands()
    webhook_url = settings.get_webhook_url
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info(f"Webhook set to {webhook_url}")
    me = await bot.get_me()
    logger.info(f"Bot started as {me.username}")


async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def create_app() -> web.Application:
    dm = DependanciesMiddleware()
    dp.message.outer_middleware(dm)
    dp.callback_query.outer_middleware(dm)
    dp.include_routers(*routers)

    app = web.Application()

    app.router.add_post("/webhook", handle_webhook)

    setup_robokassa_routes(app)

    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host=settings.site_host, port=settings.site_port)
