from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.config import Config
from app.db import Database
from app.states import AdminCheat
from app.utils import is_admin
from app.keyboards.admin import (
    admin_panel_kb,
    cheat_admin_sections_kb,
    cheat_admin_section_actions_kb,
    cheat_admin_item_actions_kb,
    confirm_delete_kb,
    done_cancel_kb,
)

r = Router()


@r.message(F.text == "🛠 Редагувати шпаргалку")
async def cheat_open_btn(message: Message, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        return
    sections = await db.list_sections()
    await message.answer("🛠 Редагування шпаргалки — розділи:", reply_markup=cheat_admin_sections_kb(sections))


@r.callback_query(F.data == "admin:cheat")
async def cheat_home(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    sections = await db.list_sections()
    await call.message.edit_text("🛠 Редагування шпаргалки — розділи:", reply_markup=cheat_admin_sections_kb(sections))
    await call.answer()


# ✅ Перемещение разделов
@r.callback_query(F.data.startswith("admin:cheat:sec_up:"))
async def section_up(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    sid = int(call.data.split(":")[-1])
    await db.move_section(sid, "up")
    sections = await db.list_sections()
    await call.message.edit_text("🛠 Редагування шпаргалки — розділи:", reply_markup=cheat_admin_sections_kb(sections))
    await call.answer("⬆️")


@r.callback_query(F.data.startswith("admin:cheat:sec_down:"))
async def section_down(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    sid = int(call.data.split(":")[-1])
    await db.move_section(sid, "down")
    sections = await db.list_sections()
    await call.message.edit_text("🛠 Редагування шпаргалки — розділи:", reply_markup=cheat_admin_sections_kb(sections))
    await call.answer("⬇️")


@r.callback_query(F.data == "admin:cheat:add_section")
async def add_section(call: CallbackQuery, state: FSMContext, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    await state.set_state(AdminCheat.creating_section)
    await call.message.reply("Введіть назву нового розділу:")
    await call.answer()


@r.message(AdminCheat.creating_section, F.text)
async def add_section_text(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Занадто коротко. Введіть нормальну назву.")
        return
    await db.create_section(title)
    await db.normalize_section_orders()
    await state.clear()
    sections = await db.list_sections()
    await message.answer("✅ Розділ додано.\n🛠 Розділи:", reply_markup=cheat_admin_sections_kb(sections))


@r.callback_query(F.data.startswith("admin:cheat:sec:"))
async def open_section(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    section_id = int(call.data.split(":")[-1])
    items = await db.list_items(section_id)
    await call.message.edit_text(
        f"📁 Розділ #{section_id}. Пункти:",
        reply_markup=cheat_admin_section_actions_kb(section_id, items),
    )
    await call.answer()


@r.callback_query(F.data.startswith("admin:cheat:rename_section:"))
async def rename_section_start(call: CallbackQuery, state: FSMContext, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    section_id = int(call.data.split(":")[-1])
    await state.set_state(AdminCheat.renaming_section)
    await state.update_data(section_id=section_id)
    await call.message.reply(f"Введіть нову назву для розділу #{section_id}:")
    await call.answer()


@r.message(AdminCheat.renaming_section, F.text)
async def rename_section_do(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    data = await state.get_data()
    section_id = int(data["section_id"])
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Занадто коротко.")
        return
    await db.rename_section(section_id, title)
    await state.clear()
    items = await db.list_items(section_id)
    await message.answer(
        f"✅ Перейменовано.\n📁 Розділ #{section_id}.",
        reply_markup=cheat_admin_section_actions_kb(section_id, items),
    )


@r.callback_query(F.data.startswith("admin:cheat:del_section:"))
async def del_section_confirm(call: CallbackQuery, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    section_id = int(call.data.split(":")[-1])
    kb = confirm_delete_kb(
        confirm_cb=f"admin:cheat:del_section_yes:{section_id}",
        cancel_cb=f"admin:cheat:sec:{section_id}",
    )
    await call.message.reply(f"Точно видалити розділ #{section_id} (і всі пункти)?", reply_markup=kb)
    await call.answer()


@r.callback_query(F.data.startswith("admin:cheat:del_section_yes:"))
async def del_section_do(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    section_id = int(call.data.split(":")[-1])
    await db.delete_section(section_id)
    await db.normalize_section_orders()
    sections = await db.list_sections()
    await call.message.reply("🗑 Видалено.\n🛠 Розділи:", reply_markup=cheat_admin_sections_kb(sections))
    await call.answer()


@r.callback_query(F.data.startswith("admin:cheat:add_item:"))
async def add_item_start(call: CallbackQuery, state: FSMContext, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    section_id = int(call.data.split(":")[-1])
    await state.set_state(AdminCheat.creating_item_title)
    await state.update_data(section_id=section_id)
    await call.message.reply(f"Введіть назву пункту для розділу #{section_id}:")
    await call.answer()


@r.message(AdminCheat.creating_item_title, F.text)
async def add_item_title(message: Message, state: FSMContext, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Занадто коротко. Введіть нормальну назву.")
        return
    await state.update_data(item_title=title, content_parts=[])
    await state.set_state(AdminCheat.creating_item_content)
    await message.answer(
        "Тепер надішліть текст пункту (можна кількома повідомленнями).\n"
        "Коли закінчите — натисніть ✅ Готово.",
        reply_markup=done_cancel_kb(),
    )


@r.message(AdminCheat.creating_item_content, F.text)
async def add_item_content(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return

    text = message.text.strip()

    if text == "⬅️ Назад":
        await state.clear()
        await message.answer("Скасовано.", reply_markup=admin_panel_kb())
        return

    if text == "✅ Готово":
        data = await state.get_data()
        section_id = int(data["section_id"])
        title = str(data["item_title"])
        parts = data.get("content_parts", [])

        if not parts:
            await message.answer("Нічого не додано. Надішліть текст або натисніть ⬅️ Назад.")
            return

        content = "\n\n".join(parts)
        await db.create_item(section_id, title, content)
        await state.clear()

        items = await db.list_items(section_id)
        await message.answer("✅ Пункт додано.", reply_markup=cheat_admin_section_actions_kb(section_id, items))
        return

    data = await state.get_data()
    parts = data.get("content_parts", [])
    parts.append(text)
    await state.update_data(content_parts=parts)

    await message.answer(
        f"Додано частину #{len(parts)}.\nМожете надіслати ще текст або натиснути ✅ Готово.",
        reply_markup=done_cancel_kb(),
    )


def _split_long_text(text: str, max_len: int = 3500) -> list[str]:
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
    if not parts and text.strip():
        raw = text.strip()
        for i in range(0, len(raw), max_len):
            parts.append(raw[i : i + max_len])
    return parts


@r.callback_query(F.data.startswith("admin:cheat:item:"))
async def open_item(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return

    item_id = int(call.data.split(":")[-1])
    it = await db.get_item(item_id)
    if not it:
        await call.answer("Не знайдено", show_alert=True)
        return

    section_id = int(it["section_id"])
    title = str(it["title"])
    content = str(it["content"])

    await call.message.answer(f"📄 <b>{title}</b>")
    for part in _split_long_text(content):
        await call.message.answer(part)

    await call.message.answer("Дії з пунктом:", reply_markup=cheat_admin_item_actions_kb(item_id, section_id))
    await call.answer()
