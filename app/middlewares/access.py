from __future__ import annotations

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message

from app.config import Config
from app.db import Database
from app.handlers.user_start import send_welcome
from app.utils import is_admin


ACCESS_PROMPT = (
    "🔐 Доступ до бота обмежено.\n\n"
    "Введіть одноразовий пароль доступу."
)


class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        db: Database | None = data.get("db")
        config: Config | None = data.get("config")
        bot: Bot | None = data.get("bot")

        if not db or not config:
            return await handler(event, data)

        user = getattr(event, "from_user", None)
        if not user:
            return await handler(event, data)

        if is_admin(user.id, config):
            await db.upsert_user(user.id)
            await db.authorize_user(user.id)
            return await handler(event, data)

        if await db.is_user_authorized(user.id):
            return await handler(event, data)

        if isinstance(event, Message):
            text = (event.text or "").strip()

            if not text or text.startswith("/start"):
                await event.answer(ACCESS_PROMPT)
                return

            if await db.check_and_use_password(text, user.id):
                await db.upsert_user(user.id)
                await event.answer("✅ Доступ відкрито.")
                if bot:
                    await send_welcome(bot, event.chat.id, config)
                return

            await event.answer("❌ Пароль невірний або вже використаний.\n\nСпробуйте ще раз.")
            return

        if isinstance(event, CallbackQuery):
            await event.answer("Спочатку введіть пароль доступу.", show_alert=True)
            return

        return await handler(event, data)
