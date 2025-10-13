import asyncio
from src.client_openai import ClientOpenAI
from src.config import settings

client = ClientOpenAI(settings.openai_key, settings.assistant_id)


async def main():
    thread = await client.get_thread("thread_GffXXxkxctCiHhux7XgdkN2Z")
    response = await client.create_message(text="Расскажи о себе", thread_id=thread.id)
    assistant_response = await client.run_assistant(thread)
    print(assistant_response)


if __name__ == "__main__":
    asyncio.run(main())
