from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states import UserTicket
from app.db import Database
from app.config import Config
from app.keyboards.user import main_menu_kb, back_kb
from app.keyboards.admin import ticket_actions_kb, admin_panel_kb
from app.utils import is_admin

r = Router()

BACK_BTN_TEXT = "⬅️ Назад"
ADMIN_BTN_TEXT = "🛠 Панель адміністратора"


async def show_main_menu(message: Message, config: Config):
    admin_flag = is_admin(message.from_user.id, config)
    await message.answer("Головне меню:", reply_markup=main_menu_kb(admin_flag))


@r.message(F.text == ADMIN_BTN_TEXT)
async def open_admin_panel(message: Message, config: Config):
    if not is_admin(message.from_user.id, config):
        return
    await message.answer("Панель адміністратора:", reply_markup=admin_panel_kb())


@r.message(F.text == "❓Анонімні питання/пропозиції/скарги")
async def ask_ticket(message: Message, state: FSMContext):
    await state.set_state(UserTicket.waiting_text)
    await message.answer(
        "Напишіть, будь ласка, ваше питання або пропозицію.\n\n"
        "Щоб вийти — натисніть «⬅️ Назад».",
        reply_markup=back_kb(),
    )


@r.message(UserTicket.waiting_text, F.text == BACK_BTN_TEXT)
async def cancel_ticket(message: Message, state: FSMContext, config: Config):
    await state.clear()
    await show_main_menu(message, config)


@r.message(UserTicket.waiting_text, F.text)
async def receive_ticket(message: Message, state: FSMContext, db: Database, config: Config):
    text = message.text.strip()

    if text == BACK_BTN_TEXT:
        return

    await db.upsert_user(message.from_user.id)

    if len(text) < 2:
        await message.answer("Повідомлення занадто коротке. Спробуйте ще раз.")
        return

    ticket_id = await db.create_ticket(message.from_user.id, text)
    await state.clear()

    await message.answer(
        f"Прийнято ✅\nНомер звернення: <b>#{ticket_id}</b>\nМи скоро відповімо.",
        reply_markup=main_menu_kb(is_admin(message.from_user.id, config)),
    )

    admin_text = (
        f"📩 <b>Нове звернення</b>\n"
        f"ID: <b>#{ticket_id}</b>\n\n"
        f"{text}"
    )

    for admin_id in config.admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                admin_text,
                reply_markup=ticket_actions_kb(ticket_id),
            )
        except Exception:
            pass


@r.message(UserTicket.waiting_text)
async def receive_ticket_nontext(message: Message):
    await message.answer(
        "Поки що приймаю лише текст.\n"
        "Надішліть повідомлення текстом або натисніть «⬅️ Назад».",
        reply_markup=back_kb(),
    )


@r.message(F.text.in_({"/id", "id", "ID"}))
async def show_id(message: Message, config: Config):
    flag = is_admin(message.from_user.id, config)
    await message.answer(f"Ваш ID: {message.from_user.id}\nАдмін: {flag}")

@r.message(F.text == "⬅️ Назад")
async def back_to_menu(message: Message, state: FSMContext, config: Config):
    # если человек НЕ в режиме ввода вопроса — просто возвращаем меню
    # если в режиме вопроса — у тебя уже есть отдельный handler, он сработает раньше
    if await state.get_state() is not None:
        # если это любой другой state (например рассылка) — сбросим
        await state.clear()

    admin_flag = is_admin(message.from_user.id, config)
    await message.answer("Головне меню:", reply_markup=main_menu_kb(admin_flag))
