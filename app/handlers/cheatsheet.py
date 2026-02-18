from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db import Database

r = Router()


def cheat_sections_kb(sections) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in sections:
        sid = int(s["id"])
        title = str(s["title"])
        kb.add(InlineKeyboardButton(text=f"📁 {title}", callback_data=f"cheat:sec:{sid}"))
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="cheat:close"))
    return kb.as_markup()


def cheat_items_kb(section_id: int, items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for it in items:
        item_id = int(it["id"])
        title = str(it["title"])
        kb.add(InlineKeyboardButton(text=f"📄 {title}", callback_data=f"cheat:item:{item_id}:{section_id}"))
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="⬅️ До розділів", callback_data="cheat:home"))
    return kb.as_markup()


def _split_long_text(text: str, max_len: int = 3500) -> list[str]:
    """
    Ріжемо по абзацах (подвійний перенос), щоб не ламати формат,
    і щоб кожен шматок гарантовано вміщався в Telegram.
    """
    blocks = text.split("\n\n")
    parts: list[str] = []
    buf = ""

    for b in blocks:
        chunk = (b + "\n\n")
        if len(buf) + len(chunk) > max_len:
            if buf.strip():
                parts.append(buf.strip())
            buf = chunk
        else:
            buf += chunk

    if buf.strip():
        parts.append(buf.strip())

    # якщо текст взагалі без абзаців і дуже довгий
    if not parts and text.strip():
        raw = text.strip()
        for i in range(0, len(raw), max_len):
            parts.append(raw[i : i + max_len])

    return parts


@r.message(F.text == "📚 Шпаргалка")
async def cheat_home_msg(message: Message, db: Database):
    sections = await db.list_sections()
    await message.answer("📚 Шпаргалка — оберіть розділ:", reply_markup=cheat_sections_kb(sections))


@r.callback_query(F.data == "cheat:home")
async def cheat_home(call: CallbackQuery, db: Database):
    sections = await db.list_sections()
    await call.message.edit_text("📚 Шпаргалка — оберіть розділ:", reply_markup=cheat_sections_kb(sections))
    await call.answer()


@r.callback_query(F.data.startswith("cheat:sec:"))
async def cheat_open_section(call: CallbackQuery, db: Database):
    section_id = int(call.data.split(":")[-1])
    items = await db.list_items(section_id)
    await call.message.edit_text(f"📁 Розділ #{section_id}. Оберіть пункт:", reply_markup=cheat_items_kb(section_id, items))
    await call.answer()


@r.callback_query(F.data.startswith("cheat:item:"))
async def cheat_open_item(call: CallbackQuery, db: Database):
    # формат: cheat:item:{item_id}:{section_id}
    parts = call.data.split(":")
    item_id = int(parts[-2])
    section_id = int(parts[-1])

    it = await db.get_item(item_id)
    if not it:
        await call.answer("Не знайдено", show_alert=True)
        return

    title = str(it["title"])
    content = str(it["content"])

    # 👉 отправляем несколькими сообщениями
    await call.message.answer(f"📄 <b>{title}</b>")

    for p in _split_long_text(content):
        await call.message.answer(p)

    # и даём кнопку назад (inline)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ Назад до пунктів", callback_data=f"cheat:sec:{section_id}"))
    await call.message.answer("—", reply_markup=kb.as_markup())

    await call.answer()


@r.callback_query(F.data == "cheat:close")
async def cheat_close(call: CallbackQuery):
    # просто закрываем inline-навигацию (убираем клаву)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.answer()
