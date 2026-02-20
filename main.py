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
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    from app.handlers._debug_mw import DebugUpdatesMiddleware
    dp.update.outer_middleware(DebugUpdatesMiddleware())

    dp["db"] = db
    dp["config"] = config

    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()  # ✅ close DB on shutdown


if __name__ == "__main__":
    asyncio.run(main())
