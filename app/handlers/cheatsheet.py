from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.db import Database
from app.keyboards.user import sections_kb, items_kb, item_back_kb

r = Router()


@r.message(F.text == "Шпаргалка")
async def show_sections(message: Message, db: Database):
    sections = await db.list_sections()
    if not sections:
        await message.answer("Поки що шпаргалка порожня.")
        return
    await message.answer("Оберіть розділ:", reply_markup=sections_kb(sections))


@r.callback_query(F.data == "cheat:back:sections")
async def back_to_sections(call: CallbackQuery, db: Database):
    sections = await db.list_sections()
    await call.message.edit_text("Оберіть розділ:", reply_markup=sections_kb(sections))
    await call.answer()


@r.callback_query(F.data.startswith("cheat:sec:"))
async def show_items(call: CallbackQuery, db: Database):
    section_id = int(call.data.split(":")[-1])
    items = await db.list_items(section_id)
    if not items:
        await call.message.edit_text("У цьому розділі поки що немає пунктів.", reply_markup=item_back_kb(section_id))
        await call.answer()
        return
    await call.message.edit_text("Оберіть пункт:", reply_markup=items_kb(section_id, items))
    await call.answer()


@r.callback_query(F.data.startswith("cheat:back:items:"))
async def back_to_items(call: CallbackQuery, db: Database):
    section_id = int(call.data.split(":")[-1])
    items = await db.list_items(section_id)
    await call.message.edit_text("Оберіть пункт:", reply_markup=items_kb(section_id, items))
    await call.answer()


@r.callback_query(F.data.startswith("cheat:item:"))
async def show_item(call: CallbackQuery, db: Database):
    item_id = int(call.data.split(":")[-1])
    it = await db.get_item(item_id)
    if not it:
        await call.answer("Пункт не знайдено", show_alert=True)
        return
    section_id = int(it["section_id"])
    text = f"<b>{it['title']}</b>

{it['content']}"
    await call.message.edit_text(text, reply_markup=item_back_kb(section_id))
    await call.answer()
