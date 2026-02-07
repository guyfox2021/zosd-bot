from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.states import AdminBroadcast
from app.db import Database
from app.config import Config
from app.utils import is_admin

r = Router()


@r.callback_query(F.data == "admin:broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    await state.set_state(AdminBroadcast.waiting_text)
    await call.message.reply("Введіть текст розсилки (одним повідомленням):")
    await call.answer()


@r.message(AdminBroadcast.waiting_text, F.text)
async def do_broadcast(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return

    text = message.text.strip()
    users = await db.list_users()
    ok = 0
    fail = 0
    for uid in users:
        try:
            await message.bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1
    await message.answer(f"Готово 📣
Надіслано: {ok}
Помилки: {fail}")
    await state.clear()


@r.message(AdminBroadcast.waiting_text)
async def broadcast_nontext(message: Message):
    await message.answer("Поки що розсилка тільки текстом.")
