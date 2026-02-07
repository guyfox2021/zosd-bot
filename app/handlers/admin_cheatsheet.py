from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.config import Config
from app.db import Database
from app.states import AdminCheat
from app.utils import is_admin
from app.keyboards.admin import (
    cheat_admin_sections_kb,
    cheat_admin_section_actions_kb,
    cheat_admin_item_actions_kb,
    confirm_delete_kb,
)

r = Router()


@r.callback_query(F.data == "admin:cheat")
async def cheat_home(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    sections = await db.list_sections()
    await call.message.edit_text("🛠 Редагування шпаргалки — розділи:", reply_markup=cheat_admin_sections_kb(sections))
    await call.answer()


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
    await state.clear()
    sections = await db.list_sections()
    await message.answer("✅ Розділ додано.
🛠 Розділи:", reply_markup=cheat_admin_sections_kb(sections))


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
        f"✅ Перейменовано.
📁 Розділ #{section_id}.",
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
    sections = await db.list_sections()
    await call.message.reply("🗑 Видалено.
🛠 Розділи:", reply_markup=cheat_admin_sections_kb(sections))
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
    await state.update_data(item_title=title)
    await state.set_state(AdminCheat.creating_item_content)
    await message.answer("Тепер введіть текст (контент) цього пункту:")


@r.message(AdminCheat.creating_item_content, F.text)
async def add_item_content(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    data = await state.get_data()
    section_id = int(data["section_id"])
    title = str(data["item_title"])
    content = message.text.strip()
    await db.create_item(section_id, title, content)
    await state.clear()
    items = await db.list_items(section_id)
    await message.answer(
        "✅ Пункт додано.",
        reply_markup=cheat_admin_section_actions_kb(section_id, items),
    )


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
    text = f"📄 <b>{it['title']}</b>

{it['content']}"
    await call.message.edit_text(text, reply_markup=cheat_admin_item_actions_kb(item_id, section_id))
    await call.answer()


@r.callback_query(F.data.startswith("admin:cheat:edit_item:"))
async def edit_item_start(call: CallbackQuery, state: FSMContext, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    item_id = int(call.data.split(":")[-1])
    it = await db.get_item(item_id)
    if not it:
        await call.answer("Не знайдено", show_alert=True)
        return
    await state.set_state(AdminCheat.editing_item_title)
    await state.update_data(item_id=item_id, section_id=int(it["section_id"]))
    await call.message.reply(f"Введіть нову назву пункту (зараз: {it['title']}):")
    await call.answer()


@r.message(AdminCheat.editing_item_title, F.text)
async def edit_item_title(message: Message, state: FSMContext, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Занадто коротко.")
        return
    await state.update_data(new_title=title)
    await state.set_state(AdminCheat.editing_item_content)
    await message.answer("Введіть новий текст (контент) пункту:")


@r.message(AdminCheat.editing_item_content, F.text)
async def edit_item_content(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    data = await state.get_data()
    item_id = int(data["item_id"])
    section_id = int(data["section_id"])
    title = str(data["new_title"])
    content = message.text.strip()
    await db.update_item(item_id, title, content)
    await state.clear()
    it = await db.get_item(item_id)
    if it:
        text = f"✅ Оновлено.

📄 <b>{it['title']}</b>

{it['content']}"
    else:
        text = "✅ Оновлено."
    await message.answer(text)


@r.callback_query(F.data.startswith("admin:cheat:del_item:"))
async def del_item_confirm(call: CallbackQuery, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    parts = call.data.split(":")
    item_id = int(parts[-2])
    section_id = int(parts[-1])
    kb = confirm_delete_kb(
        confirm_cb=f"admin:cheat:del_item_yes:{item_id}:{section_id}",
        cancel_cb=f"admin:cheat:item:{item_id}",
    )
    await call.message.reply("Точно видалити цей пункт?", reply_markup=kb)
    await call.answer()


@r.callback_query(F.data.startswith("admin:cheat:del_item_yes:"))
async def del_item_do(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    parts = call.data.split(":")
    item_id = int(parts[-2])
    section_id = int(parts[-1])
    await db.delete_item(item_id)
    items = await db.list_items(section_id)
    await call.message.reply("🗑 Видалено.", reply_markup=cheat_admin_section_actions_kb(section_id, items))
    await call.answer()
