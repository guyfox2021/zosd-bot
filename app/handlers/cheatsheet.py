from __future__ import annotations

from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db import Database

r = Router()

TELEGRAM_PHOTO_CAPTION_LIMIT = 1024
BOT_ROOT = Path(__file__).resolve().parents[2]
FACULTY_PHOTO_DIR = BOT_ROOT / "Фото" / "Факультет"

FACULTY_PEOPLE = {
    "sobko": {
        "label": "Собко",
        "aliases": ("Собко",),
        "photo": "Собко.jpg",
    },
    "vyshnevskyi": {
        "label": "Вишневський",
        "aliases": ("Вишневський", "Вишневский"),
        "photo": "Вишневський.jpg",
    },
    "lazorenko": {
        "label": "Лазоренко",
        "aliases": ("Лазоренко",),
        "photo": "Лазоренко.jpg",
    },
}


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


def leadership_folders_kb(section_id: int, source_item_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="📁 Факультету",
            callback_data=f"cheat:leadership:faculty:{source_item_id}:{section_id}",
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="📁 НАДПСУ",
            callback_data=f"cheat:leadership:nadpsu:{source_item_id}:{section_id}",
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="📁 АДПСУ",
            callback_data=f"cheat:leadership:adpsu:{source_item_id}:{section_id}",
        )
    )
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="⬅️ До розділів", callback_data="cheat:home"))
    return kb.as_markup()


def faculty_people_kb(section_id: int, source_item_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for slug, person in FACULTY_PEOPLE.items():
        kb.add(
            InlineKeyboardButton(
                text=str(person["label"]),
                callback_data=f"cheat:faculty:{slug}:{source_item_id}:{section_id}",
            )
        )
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="⬅️ До папок", callback_data=f"cheat:sec:{section_id}"))
    return kb.as_markup()


def _person_positions(text: str) -> list[tuple[int, str]]:
    lowered = text.casefold()
    positions: list[tuple[int, str]] = []
    for slug, person in FACULTY_PEOPLE.items():
        found_positions = [
            lowered.find(str(alias).casefold())
            for alias in person["aliases"]
            if lowered.find(str(alias).casefold()) >= 0
        ]
        if found_positions:
            positions.append((min(found_positions), slug))
    return sorted(positions)


def _find_faculty_source_item(items):
    for it in items:
        title = str(it["title"])
        content = str(it["content"])
        combined = f"{title}\n{content}"
        has_people = len(_person_positions(combined)) >= 2
        has_faculty_title = "керівниц" in title.casefold() and "факульт" in title.casefold()
        if has_people or has_faculty_title:
            return it
    return None


def _find_leadership_folder_items(items, folder: str, source_item_id: int):
    if folder == "nadpsu":
        keywords = ("надпсу",)
    elif folder == "adpsu":
        keywords = ("адпсу",)
    else:
        return []

    result = []
    for it in items:
        if int(it["id"]) == source_item_id:
            continue
        title = str(it["title"]).casefold()
        if any(keyword in title for keyword in keywords):
            result.append(it)
    return result


def _extract_person_info(text: str, slug: str) -> str:
    positions = _person_positions(text)
    own_index = next((idx for idx, (_, person_slug) in enumerate(positions) if person_slug == slug), None)
    if own_index is None:
        return text.strip()

    start = positions[own_index][0]
    end = positions[own_index + 1][0] if own_index + 1 < len(positions) else len(text)
    return text[start:end].strip()


def _strip_person_heading(text: str, slug: str) -> str:
    stripped = text.strip()
    lowered = stripped.casefold()
    for alias in FACULTY_PEOPLE[slug]["aliases"]:
        alias_text = str(alias)
        if lowered.startswith(alias_text.casefold()):
            rest = stripped[len(alias_text):].lstrip(" \n\r\t:-–—.,")
            return rest.strip()
    return stripped


def _fit_photo_caption(text: str) -> tuple[str, str]:
    if len(text) <= TELEGRAM_PHOTO_CAPTION_LIMIT:
        return text, ""

    cut = text.rfind("\n\n", 0, TELEGRAM_PHOTO_CAPTION_LIMIT)
    if cut < 200:
        cut = text.rfind("\n", 0, TELEGRAM_PHOTO_CAPTION_LIMIT)
    if cut < 200:
        cut = text.rfind(" ", 0, TELEGRAM_PHOTO_CAPTION_LIMIT)
    if cut < 200:
        cut = TELEGRAM_PHOTO_CAPTION_LIMIT

    return text[:cut].strip(), text[cut:].strip()


def _with_colonel_rank_at_bottom(text: str) -> str:
    lines = [line.strip() for line in text.strip().splitlines()]
    lines = [line for line in lines if line.casefold() != "полковник"]
    body = "\n".join(lines).strip()
    return f"{body}\n\nПолковник" if body else "Полковник"


async def _send_faculty_card(message: Message, slug: str, info: str):
    label = str(FACULTY_PEOPLE[slug]["label"])
    body = _with_colonel_rank_at_bottom(_strip_person_heading(info, slug))
    caption = f"<b>{label}</b>"
    if body:
        caption += f"\n\n{body}"

    first_caption, rest = _fit_photo_caption(caption)
    photo_name = str(FACULTY_PEOPLE[slug]["photo"])
    photo_path = FACULTY_PHOTO_DIR / photo_name
    if photo_path.exists():
        await message.answer_photo(FSInputFile(photo_path), caption=first_caption)
    else:
        await message.answer(first_caption)

    for part in _split_long_text(rest):
        await message.answer(part)


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
    faculty_source_item = _find_faculty_source_item(items)
    if faculty_source_item:
        await call.message.edit_text(
            "Керівництво — оберіть папку:",
            reply_markup=leadership_folders_kb(section_id, int(faculty_source_item["id"])),
        )
        await call.answer()
        return

    await call.message.edit_text(f"📁 Розділ #{section_id}. Оберіть пункт:", reply_markup=cheat_items_kb(section_id, items))
    await call.answer()


@r.callback_query(F.data.startswith("cheat:leadership:"))
async def cheat_open_leadership_folder(call: CallbackQuery, db: Database):
    # формат: cheat:leadership:{folder}:{source_item_id}:{section_id}
    parts = call.data.split(":")
    folder = parts[-3]
    source_item_id = int(parts[-2])
    section_id = int(parts[-1])

    if folder == "faculty":
        it = await db.get_item(source_item_id)
        if not it:
            await call.answer("Не знайдено", show_alert=True)
            return

        content = str(it["content"])
        for slug in FACULTY_PEOPLE:
            info = _extract_person_info(content, slug) or "Інформацію поки не додано."
            await _send_faculty_card(call.message, slug, info)

        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="⬅️ До папок", callback_data=f"cheat:sec:{section_id}"))
        await call.message.answer("—", reply_markup=kb.as_markup())
        await call.answer()
        return

    items = await db.list_items(section_id)
    folder_items = _find_leadership_folder_items(items, folder, source_item_id)
    folder_title = "НАДПСУ" if folder == "nadpsu" else "АДПСУ"

    if folder_items:
        await call.message.edit_text(
            f"Керівництво {folder_title} — оберіть пункт:",
            reply_markup=cheat_items_kb(section_id, folder_items),
        )
    else:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="⬅️ До папок", callback_data=f"cheat:sec:{section_id}"))
        await call.message.edit_text(
            f"Керівництво {folder_title}\n\nРозділ поки не наповнено.",
            reply_markup=kb.as_markup(),
        )

    await call.answer()


@r.callback_query(F.data.startswith("cheat:faculty:"))
async def cheat_open_faculty_person(call: CallbackQuery, db: Database):
    # формат: cheat:faculty:{slug}:{source_item_id}:{section_id}
    parts = call.data.split(":")
    slug = parts[-3]
    item_id = int(parts[-2])
    section_id = int(parts[-1])

    person = FACULTY_PEOPLE.get(slug)
    it = await db.get_item(item_id)
    if not person or not it:
        await call.answer("Не знайдено", show_alert=True)
        return

    content = str(it["content"])
    info = _extract_person_info(content, slug) or "Інформацію поки не додано."

    await _send_faculty_card(call.message, slug, info)

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ Назад до керівництва", callback_data=f"cheat:sec:{section_id}"))
    await call.message.answer("—", reply_markup=kb.as_markup())

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

    for slug, person in FACULTY_PEOPLE.items():
        aliases = tuple(str(alias).casefold() for alias in person["aliases"])
        if any(alias in title.casefold() for alias in aliases):
            await _send_faculty_card(call.message, slug, content)

            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text="⬅️ Назад до пунктів", callback_data=f"cheat:sec:{section_id}"))
            await call.message.answer("—", reply_markup=kb.as_markup())

            await call.answer()
            return

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
