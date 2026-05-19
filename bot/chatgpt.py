from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = (
    "You are a helpful assistant. Respond concisely in the same language the user writes in. "
    "Keep responses under 1000 characters when possible."
)


async def ask_gpt(messages: list, model: str = "gpt-3.5-turbo") -> str:
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    full_messages.extend(messages)
    r = await client.chat.completions.create(model=model, messages=full_messages)
    return r.choices[0].message.content
