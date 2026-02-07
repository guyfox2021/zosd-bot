import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.config import load_config
from app.db import Database
from app.middlewares import DbMiddleware, ConfigMiddleware
from app.routers import router


async def main():
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)

    db = Database(config.db_path)
    await db.connect()
    await db.init()

    dp = Dispatcher()
    dp.update.middleware(ConfigMiddleware(config))
    dp.update.middleware(DbMiddleware(db))

    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
