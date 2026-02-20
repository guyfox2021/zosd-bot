from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db import Database
from app.keyboards.user import main_menu_kb
from app.config import Config
from app.utils import is_admin



WELCOME_TEXT = """Вітаємо у боті факультету ЗОСД!

Тут ви можете швидко отримати навчальні матеріали, шпаргалки, актуальну інформацію та корисні довідники.

Також через бота ви можете:
✉️ поставити запитання,
💡 залишити пропозицію або ідею,
⚠️ повідомити про проблему чи неточність.

Просто обери потрібний розділ у меню або напиши своє питання — ми допоможемо знайти відповідь ✅
"""

async def send_welcome(bot: Bot, chat_id: int, config):
    admin_flag = False
    if config and hasattr(config, "admin_ids"):
        admin_flag = chat_id in set(config.admin_ids)
    from app.keyboards.user import main_menu_kb
    await bot.send_message(chat_id, WELCOME_TEXT, reply_markup=main_menu_kb(admin_flag))

r = Router()


@r.message(CommandStart())
async def start(message: Message, db: Database, config: Config):
    await db.upsert_user(message.from_user.id)

    admin_flag = is_admin(message.from_user.id, config)

    text = (
        "Вітаю! Цей бот допоможе вирішити ваші проблеми.\n\n"
        "Обери дію нижче 👇"
    )

    await send_welcome(message.bot, message.chat.id, config)
