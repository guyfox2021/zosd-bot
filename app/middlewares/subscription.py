from __future__ import annotations

import time
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramNetworkError,
)

ALLOWED_STATUSES = {"member", "administrator", "creator"}


class SubscriptionMiddleware(BaseMiddleware):

    CHANNEL_USERNAME = "@your_channel"
    CHANNEL_LINK = "https://t.me/your_channel"

    CACHE_TTL = 60

    def __init__(self):

        self.cache = {}

    def kb(self):

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 Перейти до каналу",
                        url=self.CHANNEL_LINK,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Я підписався — перевірити",
                        callback_data="sub:check",
                    )
                ],
            ]
        )

    def cache_get(self, user_id):

        v = self.cache.get(user_id)

        if not v:
            return None

        ok, expire = v

        if expire < time.time():
            self.cache.pop(user_id, None)
            return None

        return ok

    def cache_set(self, user_id, ok):

        self.cache[user_id] = (
            ok,
            time.time() + self.CACHE_TTL,
        )

    async def check(self, bot: Bot, user_id: int):

        cached = self.cache_get(user_id)

        if cached is not None:
            return cached

        try:

            member = await bot.get_chat_member(
                self.CHANNEL_USERNAME,
                user_id,
            )

            ok = member.status in ALLOWED_STATUSES

            self.cache_set(user_id, ok)

            return ok

        except (
            TelegramBadRequest,
            TelegramForbiddenError,
            TelegramRetryAfter,
            TelegramNetworkError,
        ):
            return False

    async def __call__(self, handler, event, data):

        bot: Bot = data["bot"]

        if isinstance(event, Message):

            user = event.from_user

            if not user:
                return await handler(event, data)

            ok = await self.check(bot, user.id)

            if ok:
                return await handler(event, data)

            await event.answer(
                "🔒 Підпишіться на канал.",
                reply_markup=self.kb(),
            )

            return

        if isinstance(event, CallbackQuery):

            user = event.from_user

            if not user:
                return await handler(event, data)

            # кнопка проверки
            if event.data == "sub:check":

                self.cache.pop(user.id, None)

                ok = await self.check(bot, user.id)

                if ok:

                    await event.answer("✅ Підписку підтверджено!")

                    if event.message:
                        await event.message.edit_text(
                            "✅ Доступ відкрито."
                        )

                    return await handler(event, data)

                await event.answer(
                    "❌ Ви ще не підписалися",
                    show_alert=True,
                )

                return

            ok = await self.check(bot, user.id)

            if ok:
                return await handler(event, data)

            await event.answer(
                "Спочатку підпишіться.",
                show_alert=True,
            )

            if event.message:

                try:
                    await event.message.edit_text(
                        "🔒 Підпишіться на канал.",
                        reply_markup=self.kb(),
                    )
                except TelegramBadRequest:
                    pass

            return

        return await handler(event, data)