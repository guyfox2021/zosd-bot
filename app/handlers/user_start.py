from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db import Database
from app.keyboards.user import main_menu_kb
from app.config import Config

r = Router()


@r.message(CommandStart())
async def start(message: Message, db: Database, config: Config):
    await db.upsert_user(message.from_user.id)
    text = (
        "Вітаю! Це корпоративний бот для звернень.

"
        "Обери дію нижче 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb())
