import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram.types import BotCommand
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


async def startup():
    # Настройка middleware и роутеров
    dm = DependanciesMiddleware()
    dp.message.outer_middleware(dm)
    dp.callback_query.outer_middleware(dm)
    dp.include_routers(*routers)

    # Настройка бота
    await setup_bot_commands()
    await bot.set_webhook(settings.site_url + "/webhook")
    info = await bot.get_webhook_info()
    print(info.url, info.pending_update_count)
    logger.info(f"webhook set to {settings.site_url}")
    logger.info(f"Bot started {await bot.get_me()}")


async def shutdown():
    await bot.delete_webhook()
    logger.info("Webhook deleted")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()


app = FastAPI(lifespan=lifespan)


app.add_api_route("/webhook", handle_webhook, methods=["POST"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.site_host, port=settings.site_port, reload=True
    )
