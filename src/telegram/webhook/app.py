from aiohttp import web
from aiogram.types import Update
from fastapi import FastAPI, Request
from loguru import logger

from src.config import bot, dp, settings


app = FastAPI()


@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception(f"Ошибка при обработке вебхука: {e}")
        return {"status": "error"}
