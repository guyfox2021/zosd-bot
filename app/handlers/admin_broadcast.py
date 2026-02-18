from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.states import AdminBroadcast
from app.db import Database
from app.config import Config
from app.utils import is_admin
from app.keyboards.admin import admin_panel_kb

r = Router()


def broadcast_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
    )


# ✅ Запуск рассылки по кнопке (ReplyKeyboard)
@r.message(F.text == "📣 Розсилка всім")
async def start_broadcast_btn(message: Message, state: FSMContext, config: Config):
    if not is_admin(message.from_user.id, config):
        return
    await state.set_state(AdminBroadcast.waiting_text)
    await message.answer(
        "Введіть текст розсилки (одним повідомленням).\n"
        "Щоб скасувати — натисніть ⬅️ Назад.",
        reply_markup=broadcast_cancel_kb(),
    )


# ✅ Если где-то есть inline-кнопка (не обязательно, но пусть будет)
@r.callback_query(F.data == "admin:broadcast")
async def start_broadcast_cb(call: CallbackQuery, state: FSMContext, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    await state.set_state(AdminBroadcast.waiting_text)
    await call.message.answer(
        "Введіть текст розсилки (одним повідомленням).\n"
        "Щоб скасувати — натисніть ⬅️ Назад.",
        reply_markup=broadcast_cancel_kb(),
    )
    await call.answer()


# ✅ Отмена рассылки
@r.message(AdminBroadcast.waiting_text, F.text == "⬅️ Назад")
async def cancel_broadcast(message: Message, state: FSMContext, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    await state.clear()
    await message.answer("Розсилку скасовано.", reply_markup=admin_panel_kb())


# ✅ Выполнение рассылки (только если это НЕ кнопка панели)
@r.message(AdminBroadcast.waiting_text, F.text)
async def do_broadcast(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return

    text = message.text.strip()

    # ⛔ Защита: любые кнопки панели/меню не отправляем как рассылку
    forbidden_texts = {
        "🛠 Панель адміністратора",
        "📣 Розсилка всім",
        "🛠 Редагувати шпаргалку",
        "⬅️ Назад",
        "Анонімні питання/пропозиції",
        "Шпаргалка",
    }

    if text in forbidden_texts:
        await message.answer(
            "Це кнопка меню. Розсилку скасовано, щоб не відправити зайве.",
            reply_markup=admin_panel_kb(),
        )
        await state.clear()
        return

    users = await db.list_users()

    ok, fail = 0, 0
    for uid in users:
        try:
            await message.bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1

    await state.clear()
    await message.answer(
        f"Готово 📣\nНадіслано: {ok}\nПомилки: {fail}",
        reply_markup=admin_panel_kb(),
    )


# ✅ Если админ отправил не текст (фото/файл) — не принимаем
@r.message(AdminBroadcast.waiting_text)
async def broadcast_nontext(message: Message):
    await message.answer("Розсилка поки що тільки текстом. Або натисніть ⬅️ Назад для скасування.")
