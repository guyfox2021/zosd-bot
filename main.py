import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import load_config
from app.routers import router
from app.db import Database


async def main():
    logging.basicConfig(level=logging.INFO)

    config = load_config()

    db = Database(config.db_path)
    await db.connect()   # ✅ create connection first
    await db.init()      # ✅ create tables / seed
# await db.normalize_section_orders()


    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, protect_content=True),
    )

    dp = Dispatcher()

    # These middlewares are written against Message/CallbackQuery (they use
    # isinstance() and read .from_user). Registering them on dp.update would
    # hand them the raw Update object instead, which has no .from_user and
    # isn't a Message/CallbackQuery -- every check silently no-ops and every
    # update is let through. They must be registered per event type instead.
    #
    # Access must run before Subscription so the "sub:check" callback can
    # never reach send_welcome() for a user who hasn't passed the password gate.
    from app.middlewares.access import AccessMiddleware
    from app.middlewares.subscription import SubscriptionMiddleware
    from app.handlers._debug_mw import DebugUpdatesMiddleware

    access_mw = AccessMiddleware()
    subscription_mw = SubscriptionMiddleware()
    debug_mw = DebugUpdatesMiddleware()

    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(access_mw)
        observer.outer_middleware(subscription_mw)
        observer.outer_middleware(debug_mw)

    dp["db"] = db
    dp["config"] = config

    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()  # ✅ close DB on shutdown


if __name__ == "__main__":
    asyncio.run(main())
