from .client_opneai import AssistantOpenAI
from src.config import settings

client = AssistantOpenAI(
    openai_key=settings.openai_key, assistant_id=settings.assistant_id
)
