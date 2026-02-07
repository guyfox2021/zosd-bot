from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def ticket_actions_kb(ticket_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Відповісти", callback_data=f"ticket:reply:{ticket_id}")
    return b.as_markup()


def admin_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📣 Розсилка всім", callback_data="admin:broadcast")
    b.button(text="🛠 Редагувати шпаргалку", callback_data="admin:cheat")
    b.adjust(1)
    return b.as_markup()


def cheat_admin_sections_kb(sections) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in sections:
        b.button(text=f"📁 {s['title']}", callback_data=f"admin:cheat:sec:{s['id']}")
    b.button(text="➕ Додати розділ", callback_data="admin:cheat:add_section")
    b.button(text="⬅️ Назад", callback_data="admin:home")
    b.adjust(1)
    return b.as_markup()


def cheat_admin_section_actions_kb(section_id: int, items) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for it in items:
        b.button(text=f"📄 {it['title']}", callback_data=f"admin:cheat:item:{it['id']}")
    b.button(text="➕ Додати пункт", callback_data=f"admin:cheat:add_item:{section_id}")
    b.button(text="✏️ Перейменувати розділ", callback_data=f"admin:cheat:rename_section:{section_id}")
    b.button(text="🗑 Видалити розділ", callback_data=f"admin:cheat:del_section:{section_id}")
    b.button(text="⬅️ Назад до розділів", callback_data="admin:cheat")
    b.adjust(1)
    return b.as_markup()


def cheat_admin_item_actions_kb(item_id: int, section_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Редагувати", callback_data=f"admin:cheat:edit_item:{item_id}")
    b.button(text="🗑 Видалити", callback_data=f"admin:cheat:del_item:{item_id}:{section_id}")
    b.button(text="⬅️ Назад", callback_data=f"admin:cheat:sec:{section_id}")
    b.adjust(1)
    return b.as_markup()


def confirm_delete_kb(confirm_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Так", callback_data=confirm_cb)
    b.button(text="❌ Ні", callback_data=cancel_cb)
    b.adjust(2)
    return b.as_markup()
