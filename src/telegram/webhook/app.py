from aiohttp import web
from aiogram.types import Update
from loguru import logger
from src.config import bot, dp, settings

from aiogram.webhook.aiohttp_server import setup_application


async def handle_webhook(request: web.Request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(
            bot, update
        )  # в aiogram v3 feed_update существует у экземпляра Dispatcher
        return web.Response(status=200)
    except Exception as e:
        logger.exception(f"Ошибка при обработке вебхука: {e}")
        return web.Response(status=500)
