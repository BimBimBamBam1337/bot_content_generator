from .client_opneai import AssistantOpenAI, WhisperOpenAi
from src.config import settings

post_generator = AssistantOpenAI(
    openai_key=settings.openai_key, assistant_id=settings.post_generator
)
semantic_layout_generator = AssistantOpenAI(
    openai_key=settings.openai_key, assistant_id=settings.semantic_layout_generator
)
whisper = WhisperOpenAi(openai_key=settings.openai_key)
