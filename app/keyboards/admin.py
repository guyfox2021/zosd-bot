from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def admin_panel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛠 Редагувати шпаргалку", callback_data="admin:cheat")
    kb.button(text="📣 Розсилка", callback_data="admin:broadcast")
    kb.button(text="⬅️ Назад", callback_data="admin:home")
    kb.adjust(1)
    return kb.as_markup()


def ticket_actions_kb(ticket_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✉️ Відповісти", callback_data=f"admin:reply:{ticket_id}")
    return kb.as_markup()


def confirm_delete_kb(confirm_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Так", callback_data=confirm_cb)
    kb.button(text="❌ Ні", callback_data=cancel_cb)
    kb.adjust(2)
    return kb.as_markup()


def cheat_admin_sections_kb(sections) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in sections:
        sid = int(s["id"])
        kb.row(
            InlineKeyboardButton(text=f"📁 {s['title']}", callback_data=f"admin:cheat:sec:{sid}"),
            InlineKeyboardButton(text="⬆️", callback_data=f"admin:cheat:sec_move:up:{sid}"),
            InlineKeyboardButton(text="⬇️", callback_data=f"admin:cheat:sec_move:down:{sid}"),
        )
    kb.button(text="➕ Додати розділ", callback_data="admin:cheat:add_section")
    kb.button(text="⬅️ Назад", callback_data="admin:home")
    kb.adjust(1)
    return kb.as_markup()


def cheat_admin_section_actions_kb(section_id: int, items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for it in items:
        iid = int(it["id"])
        kb.row(
            InlineKeyboardButton(text=f"📄 {it['title']}", callback_data=f"admin:cheat:item:{iid}"),
            InlineKeyboardButton(text="⬆️", callback_data=f"admin:cheat:item_move:up:{iid}:{section_id}"),
            InlineKeyboardButton(text="⬇️", callback_data=f"admin:cheat:item_move:down:{iid}:{section_id}"),
        )
    kb.button(text="➕ Додати пункт", callback_data=f"admin:cheat:add_item:{section_id}")
    kb.button(text="✏️ Перейменувати розділ", callback_data=f"admin:cheat:rename_section:{section_id}")
    kb.button(text="🗑 Видалити розділ", callback_data=f"admin:cheat:del_section:{section_id}")
    kb.button(text="⬅️ Назад", callback_data="admin:cheat")
    kb.adjust(1)
    return kb.as_markup()


def cheat_admin_item_actions_kb(item_id: int, section_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Редагувати", callback_data=f"admin:cheat:edit:{item_id}")
    kb.button(text="🗑 Видалити", callback_data=f"admin:cheat:del_item:{item_id}:{section_id}")
    kb.button(text="⬅️ До списку", callback_data=f"admin:cheat:sec:{section_id}")
    kb.adjust(1)
    return kb.as_markup()


def cheat_admin_done_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=KeyboardButton(text="✅ Готово"))
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)
