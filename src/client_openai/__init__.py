from .client_opneai import AssistantOpenAI, WhisperOpenAi
from src.config import settings

whisper = WhisperOpenAi(openai_key=settings.openai_key)
