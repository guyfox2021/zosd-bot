from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
    )


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="❓Анонімні питання/пропозиції/скарги")],
        [KeyboardButton(text="📚 Шпаргалка")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🛠 Панель адміністратора")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію…",
    )


def sections_kb(sections) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in sections:
        b.button(text=str(s["title"]), callback_data=f"cheat:sec:{s['id']}")
    b.adjust(1)
    return b.as_markup()


def items_kb(section_id: int, items) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for it in items:
        b.button(text=str(it["title"]), callback_data=f"cheat:item:{it['id']}")
    b.button(text="⬅️ Назад до розділів", callback_data="cheat:back:sections")
    b.adjust(1)
    return b.as_markup()


def item_back_kb(section_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Назад", callback_data=f"cheat:back:items:{section_id}")
    return b.as_markup()
