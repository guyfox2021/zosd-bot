import aiosqlite
from typing import Optional


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        await self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = aiosqlite.Row

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def init(self):
        assert self.conn is not None

        # Users
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                first_seen_at TEXT DEFAULT (datetime('now'))
            );"""
        )

        # Authorized users (for access control)
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS authorized_users(
                user_id INTEGER PRIMARY KEY,
                authorized_at TEXT DEFAULT (datetime('now'))
            );"""
        )

        # One-time passwords
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS access_passwords(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                password TEXT UNIQUE NOT NULL,
                used INTEGER DEFAULT 0,
                used_by_user_id INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                used_at TEXT
            );"""
        )

        # Tickets
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS tickets(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                status TEXT NOT NULL DEFAULT 'new',
                answer_text TEXT,
                answered_at TEXT
            );"""
        )

        # Cheatsheet sections & items
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS cheat_sections(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            );"""
        )
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS cheat_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(section_id) REFERENCES cheat_sections(id) ON DELETE CASCADE
            );"""
        )
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS leadership_people(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_key TEXT NOT NULL,
                full_name TEXT NOT NULL,
                position TEXT NOT NULL,
                rank TEXT NOT NULL,
                photo_path TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            );"""
        )

        await self.conn.commit()

        # Seed minimal cheatsheet if empty
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM cheat_sections;")
        row = await cur.fetchone()
        if row["c"] == 0:
            await self.conn.execute(
                "INSERT INTO cheat_sections(title, sort_order) VALUES (?, ?);",
                ("Приклад розділу", 0),
            )
            cur2 = await self.conn.execute("SELECT id FROM cheat_sections LIMIT 1;")
            sec = await cur2.fetchone()
            await self.conn.execute(
                "INSERT INTO cheat_items(section_id, title, content, sort_order) VALUES (?,?,?,?);",
                (sec["id"], "Приклад пункту", "Тут буде текст шпаргалки.", 0),
            )
            await self.conn.commit()

        await self.seed_leadership_people()
        await self.seed_access_passwords()

    # --- Users ---
    async def upsert_user(self, user_id: int):
        assert self.conn is not None
        await self.conn.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?);", (user_id,)
        )
        await self.conn.commit()

    async def list_users(self) -> list[int]:
        assert self.conn is not None
        cur = await self.conn.execute("SELECT user_id FROM users;")
        rows = await cur.fetchall()
        return [int(r["user_id"]) for r in rows]

    async def count_users(self) -> int:
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM users;")
        row = await cur.fetchone()
        return int(row["c"])

    async def count_tickets(self) -> int:
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM tickets;")
        row = await cur.fetchone()
        return int(row["c"])

    async def count_tickets_by_status(self) -> dict[str, int]:
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT status, COUNT(*) AS c FROM tickets GROUP BY status;"
        )
        rows = await cur.fetchall()
        return {str(r["status"]): int(r["c"]) for r in rows}

    async def count_ticket_authors(self) -> int:
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT COUNT(DISTINCT user_id) AS c FROM tickets;"
        )
        row = await cur.fetchone()
        return int(row["c"])

    async def top_ticket_authors(self, limit: int = 5) -> list[tuple[int, int]]:
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT user_id, COUNT(*) AS c FROM tickets GROUP BY user_id ORDER BY c DESC LIMIT ?;",
            (limit,),
        )
        rows = await cur.fetchall()
        return [(int(r["user_id"]), int(r["c"])) for r in rows]

    async def count_cheat_sections(self) -> int:
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM cheat_sections;")
        row = await cur.fetchone()
        return int(row["c"])

    async def count_cheat_items(self) -> int:
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM cheat_items;")
        row = await cur.fetchone()
        return int(row["c"])

    # --- Access Control (Passwords) ---
    async def authorize_user(self, user_id: int) -> None:
        """Add user to authorized list."""
        assert self.conn is not None
        await self.conn.execute(
            "INSERT OR IGNORE INTO authorized_users(user_id) VALUES (?);",
            (user_id,),
        )
        await self.conn.commit()

    async def is_user_authorized(self, user_id: int) -> bool:
        """Check if user is authorized."""
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT 1 FROM authorized_users WHERE user_id = ?;",
            (user_id,),
        )
        return await cur.fetchone() is not None

    async def check_and_use_password(self, password: str, user_id: int) -> bool:
        """Check if password exists and unused. If valid, mark as used and authorize user."""
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT id FROM access_passwords WHERE password = ? AND used = 0;",
            (password,),
        )
        row = await cur.fetchone()
        if not row:
            return False
        
        pwd_id = row["id"]
        await self.conn.execute(
            "UPDATE access_passwords SET used = 1, used_by_user_id = ?, used_at = datetime('now') WHERE id = ?;",
            (user_id, pwd_id),
        )
        await self.authorize_user(user_id)
        await self.conn.commit()
        return True

    async def get_unused_passwords_count(self) -> int:
        """Count unused passwords."""
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM access_passwords WHERE used = 0;"
        )
        row = await cur.fetchone()
        return int(row["c"])

    async def add_password(self, password: str) -> None:
        """Add a new password."""
        assert self.conn is not None
        await self.conn.execute(
            "INSERT INTO access_passwords(password) VALUES (?);",
            (password,),
        )
        await self.conn.commit()

    async def seed_access_passwords(self, total: int = 300) -> None:
        """Create a stock of simple one-time access passwords if the table is empty."""
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM access_passwords;")
        row = await cur.fetchone()
        if int(row["c"]) > 0:
            return

        passwords = [(f"ZOSD-{i:03d}",) for i in range(1, total + 1)]
        await self.conn.executemany(
            "INSERT OR IGNORE INTO access_passwords(password) VALUES (?);",
            passwords,
        )
        await self.conn.commit()

    async def count_authorized_users(self) -> int:
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM authorized_users;")
        row = await cur.fetchone()
        return int(row["c"])

    # --- Tickets ---
    async def create_ticket(self, user_id: int, text: str) -> int:
        assert self.conn is not None
        cur = await self.conn.execute(
            "INSERT INTO tickets(user_id, text) VALUES(?, ?);",
            (user_id, text),
        )
        await self.conn.commit()
        return int(cur.lastrowid)

    async def get_ticket(self, ticket_id: int):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT * FROM tickets WHERE id = ?;", (ticket_id,)
        )
        return await cur.fetchone()

    async def answer_ticket(self, ticket_id: int, answer_text: str):
        assert self.conn is not None
        await self.conn.execute(
            """UPDATE tickets
               SET status='answered', answer_text=?, answered_at=datetime('now')
               WHERE id=?;""",
            (answer_text, ticket_id),
        )
        await self.conn.commit()

    # --- Cheatsheet (user) ---
    async def list_sections(self):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT * FROM cheat_sections ORDER BY sort_order, id;"
        )
        return await cur.fetchall()

    async def list_items(self, section_id: int):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT * FROM cheat_items WHERE section_id=? ORDER BY sort_order, id;",
            (section_id,),
        )
        return await cur.fetchall()

    async def get_item(self, item_id: int):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT * FROM cheat_items WHERE id=?;", (item_id,)
        )
        return await cur.fetchone()

    # --- Leadership cards ---
    async def seed_leadership_people(self):
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM leadership_people;")
        row = await cur.fetchone()
        if int(row["c"]) > 0:
            return

        people = [
            ("faculty", "СОБКО Вадим Григорович", "Начальник (декан) факультету забезпечення оперативно-службової діяльності", "Полковник", "Фото/Факультет/Собко.jpg", 0),
            ("faculty", "ЛАЗОРЕНКО Олександр Васильович", "Заступник начальника (заступник декана) факультету забезпечення оперативно-службової діяльності з навчально-методичної роботи", "Полковник", "Фото/Факультет/Лазоренко.jpg", 1),
            ("faculty", "ВИШНЕВСЬКИЙ Володимир Анатолійович", "Заступник начальника (заступник декана) факультету забезпечення оперативно-службової діяльності з морально-психологічного забезпечення", "Полковник", "Фото/Факультет/Вишневський.jpg", 2),
            ("adpsu", "ВАВРИНЮК Валерій Павлович", "Тимчасово виконуючий  обов'язки Голови Державної прикордонної служби України", "Генерал-майор", "Фото/АДПСУ/ВАВРИНЮК.jpg", 0),
            ("adpsu", "ЧЕНЧИК Вадим Миколайович", "Заступник Голови Державної прикордонної служби України", "Генерал-майор", "Фото/АДПСУ/ЧЕНЧИК.jpg", 1),
            ("adpsu", "СЕРДЮК Сергій Іванович", "Заступник Голови Державної прикордонної служби України", "Генерал-майор", "Фото/АДПСУ/СЕРДЮК.jpg", 2),
            ("nadpsu", "Мейко Олександр Васильович", "Ректор Національної академії Державної прикордонної служби України", "Полковник", "Фото/НАДПСУ/МЕЙКО.jpg", 0),
            ("nadpsu", "Білявець Сергій Якович", "Заступник ректора (проректор) з наукової роботи Національної академії Державної прикордонної служби України", "Полковник", "Фото/НАДПСУ/БІЛЯВЕЦЬ.jpg", 1),
            ("nadpsu", "Лисак Павло Петрович", "Заступник ректора (проректор) з морально-психологічного забезпечення Національної академії Державної прикордонної служби України", "Полковник", "Фото/НАДПСУ/ЛИСАК.jpg", 2),
            ("nadpsu", "Сулима Віктор Миколайович", "Заступник ректора (проректор) з озброєння та техніки Національної академії Державної прикордонної служби України", "Полковник", "Фото/НАДПСУ/СУЛИМА.jpg", 3),
            ("nadpsu", "Мовчан Сергій Васильович", "Заступник ректора (проректор) з матеріального забезпечення Національної академії Державної прикордонної служби України", "Полковник", "Фото/НАДПСУ/МОВЧАН.jpg", 4),
        ]
        await self.conn.executemany(
            """INSERT INTO leadership_people(group_key, full_name, position, rank, photo_path, sort_order)
               VALUES (?, ?, ?, ?, ?, ?);""",
            people,
        )
        await self.conn.commit()

    async def list_leadership_people(self, group_key: str):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT * FROM leadership_people WHERE group_key=? ORDER BY sort_order, id;",
            (group_key,),
        )
        return await cur.fetchall()

    async def get_leadership_person(self, person_id: int):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT * FROM leadership_people WHERE id=?;",
            (person_id,),
        )
        return await cur.fetchone()

    async def update_leadership_field(self, person_id: int, field: str, value: str):
        assert self.conn is not None
        allowed = {"full_name", "position", "rank", "photo_path"}
        if field not in allowed:
            raise ValueError("Invalid leadership field")
        await self.conn.execute(
            f"UPDATE leadership_people SET {field}=? WHERE id=?;",
            (value, person_id),
        )
        await self.conn.commit()

    async def create_leadership_person(self, group_key: str, full_name: str, position: str, rank: str, photo_path: str):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order FROM leadership_people WHERE group_key=?;",
            (group_key,),
        )
        row = await cur.fetchone()
        await self.conn.execute(
            """INSERT INTO leadership_people(group_key, full_name, position, rank, photo_path, sort_order)
               VALUES (?, ?, ?, ?, ?, ?);""",
            (group_key, full_name, position, rank, photo_path, int(row["next_order"])),
        )
        await self.conn.commit()

    # --- Cheatsheet (admin) ---
    async def create_section(self, title: str):
        assert self.conn is not None
        await self.conn.execute(
            "INSERT INTO cheat_sections(title, sort_order) VALUES(?, 0);",
            (title,),
        )
        await self.conn.commit()

    async def rename_section(self, section_id: int, title: str):
        assert self.conn is not None
        await self.conn.execute(
            "UPDATE cheat_sections SET title=? WHERE id=?;",
            (title, section_id),
        )
        await self.conn.commit()

    async def delete_section(self, section_id: int):
        assert self.conn is not None
        await self.conn.execute("DELETE FROM cheat_sections WHERE id=?;", (section_id,))
        await self.conn.commit()

    async def create_item(self, section_id: int, title: str, content: str):
        assert self.conn is not None
        await self.conn.execute(
            "INSERT INTO cheat_items(section_id, title, content, sort_order) VALUES(?,?,?,0);",
            (section_id, title, content),
        )
        await self.conn.commit()

    async def update_item(self, item_id: int, title: str, content: str):
        assert self.conn is not None
        await self.conn.execute(
            "UPDATE cheat_items SET title=?, content=? WHERE id=?;",
            (title, content, item_id),
        )
        await self.conn.commit()

    async def delete_item(self, item_id: int):
        assert self.conn is not None
        await self.conn.execute("DELETE FROM cheat_items WHERE id=?;", (item_id,))
        await self.conn.commit()

    # --- Ordering: items (within section) ---
    async def normalize_item_orders(self, section_id: int):
        """Выровнять sort_order для пунктов раздела: 0..N по текущей сортировке."""
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT id FROM cheat_items WHERE section_id=? ORDER BY sort_order, id;",
            (section_id,),
        )
        rows = await cur.fetchall()
        for i, r in enumerate(rows):
            await self.conn.execute(
                "UPDATE cheat_items SET sort_order=? WHERE id=?;",
                (i, int(r["id"])),
            )
        await self.conn.commit()

    async def move_item(self, item_id: int, section_id: int, direction: str):
        """
        direction: 'up' | 'down'
        Меняем местами sort_order с соседним пунктом в этом же разделе.
        """
        assert self.conn is not None

        cur = await self.conn.execute(
            "SELECT id, sort_order FROM cheat_items WHERE id=? AND section_id=?;",
            (item_id, section_id),
        )
        row = await cur.fetchone()
        if not row:
            return

        so = int(row["sort_order"])

        if direction == "up":
            cur2 = await self.conn.execute(
                """SELECT id, sort_order FROM cheat_items
                   WHERE section_id=? AND sort_order < ?
                   ORDER BY sort_order DESC, id DESC
                   LIMIT 1;""",
                (section_id, so),
            )
        else:
            cur2 = await self.conn.execute(
                """SELECT id, sort_order FROM cheat_items
                   WHERE section_id=? AND sort_order > ?
                   ORDER BY sort_order ASC, id ASC
                   LIMIT 1;""",
                (section_id, so),
            )

        neigh = await cur2.fetchone()
        if not neigh:
            return

        n_id = int(neigh["id"])
        n_so = int(neigh["sort_order"])

        # swap
        await self.conn.execute("UPDATE cheat_items SET sort_order=? WHERE id=?;", (n_so, item_id))
        await self.conn.execute("UPDATE cheat_items SET sort_order=? WHERE id=?;", (so, n_id))
        await self.conn.commit()
