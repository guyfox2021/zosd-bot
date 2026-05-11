from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🛠 Редагувати шпаргалку", callback_data="admin:cheat"),
    )
    kb.row(
        InlineKeyboardButton(text="📣 Розсилка всім", callback_data="admin:broadcast"),
    )
    kb.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
    )
    return kb.as_markup()


def ticket_actions_kb(ticket_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✉️ Відповісти", callback_data=f"admin:reply:{ticket_id}"),
    )
    return kb.as_markup()


def cheat_admin_sections_kb(sections) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="👥 Керівництво", callback_data="admin:leadership"))
    for s in sections:
        sid = int(s["id"])
        title = str(s["title"])
        kb.row(InlineKeyboardButton(text=f"📁 {title}", callback_data=f"admin:cheat:sec:{sid}"))
    kb.row(InlineKeyboardButton(text="➕ Додати розділ", callback_data="admin:cheat:add_section"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:home"))
    return kb.as_markup()


def cheat_admin_section_actions_kb(section_id: int, items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for it in items:
        item_id = int(it["id"])
        title = str(it["title"])
        kb.row(
            InlineKeyboardButton(text=f"📄 {title}", callback_data=f"admin:cheat:item:{item_id}"),
        )

    kb.row(InlineKeyboardButton(text="➕ Додати пункт", callback_data=f"admin:cheat:add_item:{section_id}"))
    kb.row(InlineKeyboardButton(text="✏️ Перейменувати розділ", callback_data=f"admin:cheat:rename_section:{section_id}"))
    kb.row(InlineKeyboardButton(text="🗑 Видалити розділ", callback_data=f"admin:cheat:del_section:{section_id}"))
    kb.row(InlineKeyboardButton(text="⬅️ До розділів", callback_data="admin:cheat"))
    return kb.as_markup()


def cheat_admin_item_actions_kb(item_id: int, section_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # ⬆️⬇️ перемещение пункта внутри раздела
    kb.row(
        InlineKeyboardButton(
            text="⬆️ Підняти пункт",
            callback_data=f"admin:cheat:item_move:up:{item_id}:{section_id}",
        ),
        InlineKeyboardButton(
            text="⬇️ Опустити пункт",
            callback_data=f"admin:cheat:item_move:down:{item_id}:{section_id}",
        ),
    )

    kb.row(InlineKeyboardButton(text="✏️ Редагувати", callback_data=f"admin:cheat:edit_item:{item_id}"))
    kb.row(InlineKeyboardButton(text="🗑 Видалити", callback_data=f"admin:cheat:del_item:{item_id}:{section_id}"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:cheat:sec:{section_id}"))
    return kb.as_markup()


def confirm_delete_kb(confirm_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Так", callback_data=confirm_cb),
        InlineKeyboardButton(text="❌ Ні", callback_data=cancel_cb),
    )
    return kb.as_markup()


def leadership_groups_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📁 Факультету", callback_data="admin:leadership:group:faculty"))
    kb.row(InlineKeyboardButton(text="📁 НАДПСУ", callback_data="admin:leadership:group:nadpsu"))
    kb.row(InlineKeyboardButton(text="📁 АДПСУ", callback_data="admin:leadership:group:adpsu"))
    kb.row(InlineKeyboardButton(text="⬅️ До шпаргалки", callback_data="admin:cheat"))
    return kb.as_markup()


def leadership_people_kb(group_key: str, people) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for person in people:
        kb.row(
            InlineKeyboardButton(
                text=str(person["full_name"]),
                callback_data=f"admin:leadership:person:{person['id']}",
            )
        )
    kb.row(InlineKeyboardButton(text="➕ Додати людину", callback_data=f"admin:leadership:add:{group_key}"))
    kb.row(InlineKeyboardButton(text="⬅️ До груп", callback_data="admin:leadership"))
    return kb.as_markup()


def leadership_person_kb(person_id: int, group_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✏️ ПІБ", callback_data=f"admin:leadership:edit:{person_id}:full_name"))
    kb.row(InlineKeyboardButton(text="✏️ Посада", callback_data=f"admin:leadership:edit:{person_id}:position"))
    kb.row(InlineKeyboardButton(text="✏️ Звання", callback_data=f"admin:leadership:edit:{person_id}:rank"))
    kb.row(InlineKeyboardButton(text="✏️ Фото", callback_data=f"admin:leadership:edit:{person_id}:photo_path"))
    kb.row(InlineKeyboardButton(text="⬅️ До списку", callback_data=f"admin:leadership:group:{group_key}"))
    return kb.as_markup()
