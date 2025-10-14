import asyncio

from openai import AsyncOpenAI
from openai.resources.beta.threads.messages import Messages
from openai.types.beta import Thread
from openai.types.beta.threads import Message

from src.config import settings


class ClientOpenAI:
    def __init__(self, openai_key: str, assistant_id: str) -> None:
        self.client = AsyncOpenAI(api_key=openai_key)
        self.assistant_id = assistant_id

    async def create_thread(self) -> Thread:
        thread = await self.client.beta.threads.create()
        return thread

    async def get_thread(self, thread_id: str) -> Thread:
        thread = await self.client.beta.threads.retrieve(thread_id=thread_id)
        return thread

    async def create_message(
        self, text: str, thread_id: str, role: str = "user"
    ) -> Message:
        message = await self.client.beta.threads.messages.create(
            thread_id=thread_id, role=role, content=text
        )
        return message

    async def get_thread_messages(self, thread_id: str) -> list[Message]:
        thread_messages = await self.client.beta.threads.messages.list(
            thread_id=thread_id
        )
        return thread_messages.data

    async def run_assistant(self, thread: Thread) -> str:
        assistant = await self.client.beta.assistants.retrieve(
            assistant_id=self.assistant_id
        )
        run = await self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id
        )
        while run.status != "completed":
            await asyncio.sleep(0.5)
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
        message = await self.client.beta.threads.messages.list(thread_id=thread.id)
        new_message = message.data[0].content[0].text.value
        return new_message


client = ClientOpenAI(
    openai_key=settings.openai_key, assistant_id=settings.assistant_id
)
