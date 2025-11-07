import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram.types import BotCommand
from loguru import logger

from src.config import dp, bot, settings
from src.telegram.midlewares import DependanciesMiddleware
from src.telegram.handlers import routers
from src.telegram.webhook import robokassa_result


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

    await setup_bot_commands()
    asyncio.create_task(dp.start_polling(bot))


async def shutdown():
    await bot.delete_webhook()
    await bot.close()
    logger.info("Webhook deleted")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()


app = FastAPI(lifespan=lifespan)


app.add_api_route("/robokassa/result", robokassa_result, methods=["POST"])
