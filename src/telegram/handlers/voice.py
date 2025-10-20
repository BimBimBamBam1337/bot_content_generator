import aiohttp
import os

from aiogram import Router, F
from aiogram.types import Message

from src.client_openai import whisper
from src.constants import TMP_DIR

router = Router()


@router.message(F.voice)
async def handle_voice_message(message: Message, bot):
    file = await bot.get_file(message.voice.file_id)
    file_path = file.file_path

    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
    local_path = TMP_DIR / f"{message.from_user.id}.ogg"

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open(local_path, "wb") as f:
                    f.write(await resp.read())

    transcription = await whisper.get_transcription(str(local_path))

    await message.answer(f"🗣 Распознанный текст:\n\n{transcription}")

    os.remove(local_path)
