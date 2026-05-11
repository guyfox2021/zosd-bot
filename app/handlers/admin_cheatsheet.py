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
    leadership_groups_kb,
    leadership_people_kb,
    leadership_person_kb,
)

r = Router()

LEADERSHIP_GROUP_LABELS = {
    "faculty": "Факультету",
    "nadpsu": "НАДПСУ",
    "adpsu": "АДПСУ",
}

LEADERSHIP_FIELD_LABELS = {
    "full_name": "ПІБ",
    "position": "посада",
    "rank": "звання",
    "photo_path": "шлях до фото",
}


def _split_text(text: str, limit: int = 3500) -> list[str]:
    """Разбиваем длинный текст на части, чтобы Telegram не резал сообщение."""
    if not text:
        return [""]
    parts = []
    cur = ""
    for line in text.splitlines(True):
        if len(cur) + len(line) > limit:
            parts.append(cur)
            cur = ""
        cur += line
    if cur:
        parts.append(cur)
    return parts


# =========================
# HOME / SECTIONS
# =========================

@r.callback_query(F.data == "admin:cheat")
async def cheat_home(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    sections = await db.list_sections()
    await call.message.edit_text(
        "🛠 Редагування шпаргалки — розділи:",
        reply_markup=cheat_admin_sections_kb(sections),
    )
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
    await message.answer("✅ Розділ додано.", reply_markup=cheat_admin_sections_kb(sections))


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
        cancel_cb="admin:cheat",
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
    await call.message.reply("🗑 Видалено.", reply_markup=cheat_admin_sections_kb(sections))
    await call.answer()


# =========================
# ITEMS (ВАЖНО: порядок!)
# =========================

@r.callback_query(F.data == "admin:leadership")
async def leadership_home(call: CallbackQuery, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    await call.message.edit_text("👥 Редагування керівництва — оберіть групу:", reply_markup=leadership_groups_kb())
    await call.answer()


@r.callback_query(F.data.startswith("admin:leadership:group:"))
async def leadership_group(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    group_key = call.data.split(":")[-1]
    people = await db.list_leadership_people(group_key)
    group_label = LEADERSHIP_GROUP_LABELS.get(group_key, group_key)
    await call.message.edit_text(
        f"👥 Керівництво {group_label} — оберіть людину:",
        reply_markup=leadership_people_kb(group_key, people),
    )
    await call.answer()


@r.callback_query(F.data.startswith("admin:leadership:person:"))
async def leadership_person(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    person_id = int(call.data.split(":")[-1])
    person = await db.get_leadership_person(person_id)
    if not person:
        await call.answer("Не знайдено", show_alert=True)
        return
    text = (
        f"<b>{person['full_name']}</b>\n\n"
        f"{person['position']}\n\n"
        f"{person['rank']}\n\n"
        f"Фото: <code>{person['photo_path']}</code>"
    )
    await call.message.edit_text(
        text,
        reply_markup=leadership_person_kb(person_id, str(person["group_key"])),
    )
    await call.answer()


@r.callback_query(F.data.startswith("admin:leadership:edit:"))
async def leadership_edit_start(call: CallbackQuery, state: FSMContext, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    parts = call.data.split(":")
    person_id = int(parts[-2])
    field = parts[-1]
    person = await db.get_leadership_person(person_id)
    if not person or field not in LEADERSHIP_FIELD_LABELS:
        await call.answer("Не знайдено", show_alert=True)
        return
    await state.set_state(AdminCheat.editing_leadership_field)
    await state.update_data(person_id=person_id, field=field)
    await call.message.answer(
        f"Введіть нове значення для поля <b>{LEADERSHIP_FIELD_LABELS[field]}</b>.\n\n"
        f"Зараз:\n{person[field]}"
    )
    await call.answer()


@r.callback_query(F.data.startswith("admin:leadership:add:"))
async def leadership_add_start(call: CallbackQuery, state: FSMContext, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return
    group_key = call.data.split(":")[-1]
    if group_key not in LEADERSHIP_GROUP_LABELS:
        await call.answer("Не знайдено", show_alert=True)
        return
    await state.set_state(AdminCheat.creating_leadership_full_name)
    await state.update_data(group_key=group_key)
    await call.message.answer("Введіть ПІБ:")
    await call.answer()


@r.message(AdminCheat.creating_leadership_full_name, F.text)
async def leadership_add_full_name(message: Message, state: FSMContext, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    value = message.text.strip()
    if len(value) < 2:
        await message.answer("Занадто коротко. Введіть ПІБ.")
        return
    await state.update_data(full_name=value)
    await state.set_state(AdminCheat.creating_leadership_position)
    await message.answer("Введіть посаду:")


@r.message(AdminCheat.creating_leadership_position, F.text)
async def leadership_add_position(message: Message, state: FSMContext, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    value = message.text.strip()
    if len(value) < 2:
        await message.answer("Занадто коротко. Введіть посаду.")
        return
    await state.update_data(position=value)
    await state.set_state(AdminCheat.creating_leadership_rank)
    await message.answer("Введіть звання:")


@r.message(AdminCheat.creating_leadership_rank, F.text)
async def leadership_add_rank(message: Message, state: FSMContext, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    value = message.text.strip()
    if len(value) < 1:
        await message.answer("Введіть звання.")
        return
    await state.update_data(rank=value)
    await state.set_state(AdminCheat.creating_leadership_photo)
    await message.answer("Введіть шлях до фото, наприклад: Фото/АДПСУ/ПІБ.jpg")


@r.message(AdminCheat.creating_leadership_photo, F.text)
async def leadership_add_photo(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    data = await state.get_data()
    photo_path = message.text.strip()
    await db.create_leadership_person(
        str(data["group_key"]),
        str(data["full_name"]),
        str(data["position"]),
        str(data["rank"]),
        photo_path,
    )
    await state.clear()
    people = await db.list_leadership_people(str(data["group_key"]))
    await message.answer(
        "✅ Людину додано.",
        reply_markup=leadership_people_kb(str(data["group_key"]), people),
    )


@r.message(AdminCheat.editing_leadership_field, F.text)
async def leadership_edit_save(message: Message, state: FSMContext, db: Database, config: Config):
    if not is_admin(message.from_user.id, config):
        await state.clear()
        return
    data = await state.get_data()
    person_id = int(data["person_id"])
    field = str(data["field"])
    value = message.text.strip()
    if len(value) < 1:
        await message.answer("Порожнє значення. Введіть текст.")
        return
    await db.update_leadership_field(person_id, field, value)
    await state.clear()
    person = await db.get_leadership_person(person_id)
    await message.answer(
        "✅ Оновлено.",
        reply_markup=leadership_person_kb(person_id, str(person["group_key"])),
    )

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
    await db.normalize_item_orders(section_id)

    await state.clear()
    items = await db.list_items(section_id)
    await message.answer("✅ Пункт додано.", reply_markup=cheat_admin_section_actions_kb(section_id, items))


# ---- 1) edit_item (ДОЛЖНО БЫТЬ ВЫШЕ item:)
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
    await call.message.answer(f"✏️ Введіть нову назву пункту (зараз: {it['title']}):")
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
    await db.normalize_item_orders(section_id)

    await state.clear()
    await message.answer("✅ Оновлено.")


# ---- 2) move item (ДОЛЖНО БЫТЬ ВЫШЕ item:)
@r.callback_query(F.data.startswith("admin:cheat:item_move:"))
async def item_move(call: CallbackQuery, db: Database, config: Config):
    if not is_admin(call.from_user.id, config):
        await call.answer("Немає доступу", show_alert=True)
        return

    # admin:cheat:item_move:up:55:12
    parts = call.data.split(":")
    direction = parts[-3]  # up/down
    item_id = int(parts[-2])
    section_id = int(parts[-1])

    await db.move_item(item_id, section_id, "up" if direction == "up" else "down")

    items = await db.list_items(section_id)
    await call.message.edit_reply_markup(
    	reply_markup=cheat_admin_section_actions_kb(section_id, items)
    )

    await call.answer("⬆️ Пункт піднято" if direction == "up" else "⬇️ Пункт опущено")



# ---- 3) open item (ПОСЛЕ edit/move)
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

    # Отправляем контент кусками (если длинный), потом отдельное сообщение с кнопками.
    await call.message.answer(f"📄 <b>{title}</b>")
    for part in _split_text(content, 3500):
        if part.strip():
            await call.message.answer(part)

    await call.message.answer(
        "Керування пунктом:",
        reply_markup=cheat_admin_item_actions_kb(item_id, section_id),
    )
    await call.answer()


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
    await db.normalize_item_orders(section_id)

    items = await db.list_items(section_id)
    await call.message.reply("🗑 Видалено.", reply_markup=cheat_admin_section_actions_kb(section_id, items))
    await call.answer()
