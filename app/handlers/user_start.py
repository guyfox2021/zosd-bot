from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db import Database
from app.keyboards.user import main_menu_kb
from app.config import Config
from app.utils import is_admin

r = Router()


@r.message(CommandStart())
async def start(message: Message, db: Database, config: Config):
    await db.upsert_user(message.from_user.id)

    admin_flag = is_admin(message.from_user.id, config)

    text = (
        "Вітаю! Цей бот допоможе вирішити ваші проблеми.\n\n"
        "Обери дію нижче 👇"
    )

    await message.answer(text, reply_markup=main_menu_kb(admin_flag))
