from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

class DebugUpdatesMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery):
            print("🧩 MW CALLBACK:", event.data)
        elif isinstance(event, Message):
            print("💬 MW MESSAGE:", event.text)
        return await handler(event, data)
