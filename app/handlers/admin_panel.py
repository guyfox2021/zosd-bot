from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from app.config import Config
from app.keyboards.admin import admin_panel_kb
from app.utils import is_admin

r = Router()


@r.callback_query(F.data == "admin:home")
async def admin_home(call: CallbackQuery, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return

    # ✅ ReplyKeyboardMarkup нельзя использовать в edit_text — только в answer()
    await call.message.answer("Панель адміністратора:", reply_markup=admin_panel_kb())
    await call.answer()


# ✅ На всякий случай: если вход в админку происходит через команду или кнопку-текст
@r.message(F.text.in_({"🛠 Панель адміністратора", "Панель адміністратора", "/admin"}))
async def admin_home_msg(message: Message, config: Config):
    if not is_admin(message.from_user.id, config):
        return
    await message.answer("Панель адміністратора:", reply_markup=admin_panel_kb())
