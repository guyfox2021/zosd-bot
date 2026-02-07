from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states import UserTicket
from app.db import Database
from app.config import Config
from app.keyboards.user import main_menu_kb
from app.keyboards.admin import ticket_actions_kb, admin_panel_kb
from app.utils import is_admin

r = Router()


@r.message(F.text == "Анонімні питання/пропозиції")
async def ask_ticket(message: Message, state: FSMContext):
    await state.set_state(UserTicket.waiting_text)
    await message.answer(
        "Напишіть, будь ласка, ваше питання або пропозицію.
"
        "Ми відповімо максимально оперативно та врахуємо вашу пропозицію.",
        reply_markup=main_menu_kb(),
    )


@r.message(UserTicket.waiting_text, F.text)
async def receive_ticket(message: Message, state: FSMContext, db: Database, config: Config):
    await db.upsert_user(message.from_user.id)
    text = message.text.strip()
    if len(text) < 2:
        await message.answer("Повідомлення занадто коротке. Спробуйте ще раз.")
        return

    ticket_id = await db.create_ticket(message.from_user.id, text)
    await state.clear()

    await message.answer(f"Прийнято ✅
Номер звернення: <b>#{ticket_id}</b>
Ми скоро відповімо.", reply_markup=main_menu_kb())

    # notify admins
    admin_text = (
        f"📩 <b>Нове звернення</b>
"
        f"ID: <b>#{ticket_id}</b>

"
        f"{text}"
    )
    for admin_id in config.admin_ids:
        try:
            await message.bot.send_message(
                admin_id, admin_text, reply_markup=ticket_actions_kb(ticket_id)
            )
        except Exception:
            # ignore blocked/unreachable admins
            pass


@r.message(UserTicket.waiting_text)
async def receive_ticket_nontext(message: Message):
    await message.answer("Поки що приймаю лише текст. Надішліть повідомлення текстом 🙂")


@r.message(F.text.in_({"Адмін", "Админ", "Admin", "/admin"}))
async def admin_entry(message: Message, config: Config):
    if not is_admin(message.from_user.id, config):
        return
    await message.answer("Панель адміністратора:", reply_markup=admin_panel_kb())
