import os

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage

from src.config.settings import settings

dp = Dispatcher(storage=RedisStorage.from_url(str(os.getenv("REDIS_URL")) + "/0"))
bot = Bot(settings.token)
