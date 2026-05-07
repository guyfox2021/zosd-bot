from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from app.config import Config
from app.db import Database
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
@r.callback_query(F.data == "admin:stats")
async def admin_stats(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return

    total_users = await db.count_users()
    total_tickets = await db.count_tickets()
    status_counts = await db.count_tickets_by_status()
    ticket_authors = await db.count_ticket_authors()
    total_sections = await db.count_cheat_sections()
    total_items = await db.count_cheat_items()
    top_users = await db.top_ticket_authors(limit=5)

    answered = status_counts.get("answered", 0)
    new = status_counts.get("new", 0)
    other = total_tickets - answered - new
    average_per_active = round(total_tickets / ticket_authors, 2) if ticket_authors else 0

    lines = [
        "📊 Статистика робочого бота:",
        f"🔹 Зареєстрованих користувачів: {total_users}",
        f"🔹 Користувачів, які писали питання: {ticket_authors}",
        f"🔹 Всього звернень: {total_tickets}",
        f"    • Нових: {new}",
        f"    • Відповіли: {answered}",
    ]

    if other:
        lines.append(f"    • Інші статуси: {other}")

    lines.extend([
        f"🔹 Середня кількість звернень на активного користувача: {average_per_active}",
        f"🔹 Розділів шпаргалки: {total_sections}",
        f"🔹 Пунктів шпаргалки: {total_items}",
    ])

    if top_users:
        lines.append("\nТоп користувачів за кількістю звернень:")
        for idx, (user_id, count) in enumerate(top_users, start=1):
            lines.append(f"    {idx}. ID {user_id}: {count}")

    await call.message.answer("\n".join(lines), reply_markup=admin_panel_kb())
    await call.answer()


@r.message(F.text.in_({"🛠 Панель адміністратора", "Панель адміністратора", "/admin"}))
async def admin_home_msg(message: Message, config: Config):
    if not is_admin(message.from_user.id, config):
        return
    await message.answer("Панель адміністратора:", reply_markup=admin_panel_kb())
