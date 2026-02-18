from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.states import AdminReply
from app.db import Database
from app.config import Config
from app.utils import is_admin

r = Router()


@r.callback_query(F.data.startswith("ticket:reply:"))
async def start_reply(call: CallbackQuery, state: FSMContext, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return

    ticket_id = int(call.data.split(":")[-1])
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await call.answer("Звернення не знайдено", show_alert=True)
        return

    await state.set_state(AdminReply.waiting_answer)
    await state.update_data(ticket_id=ticket_id)

    await call.answer()
    await call.message.reply(f"Введіть відповідь для звернення <b>#{ticket_id}</b> (одним повідомленням):")


@r.message(AdminReply.waiting_answer, F.text)
async def send_answer(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return

    data = await state.get_data()
    ticket_id = int(data["ticket_id"])
    answer = message.text.strip()

    if len(answer) < 1:
        await message.answer("Відповідь порожня. Спробуйте ще раз.")
        return

    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await message.answer("Звернення не знайдено.")
        await state.clear()
        return

    await db.answer_ticket(ticket_id, answer)
    user_id = int(ticket["user_id"])

    try:
        await message.bot.send_message(
            user_id,
            f"✅ Відповідь на звернення <b>#{ticket_id}</b>:\n\n{answer}",
        )
    except Exception:
        await message.answer("⚠️ Не вдалося надіслати відповідь користувачу (можливо, він заблокував бота).")
        await state.clear()
        return

    await message.answer(f"Відправлено ✅ (звернення #{ticket_id})")
    await state.clear()


@r.message(AdminReply.waiting_answer)
async def answer_nontext(message: Message):
    await message.answer("Надішліть відповідь текстом.")
