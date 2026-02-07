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
    await call.message.edit_text("Панель адміністратора:", reply_markup=admin_panel_kb())
    await call.answer()
