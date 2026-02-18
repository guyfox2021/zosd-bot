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

    # --- Ordering: sections ---
    async def normalize_section_orders(self):
        """Выровнять sort_order для всех разделов: 0..N по текущей сортировке."""
        assert self.conn is not None
        cur = await self.conn.execute("SELECT id FROM cheat_sections ORDER BY sort_order, id;")
        rows = await cur.fetchall()
        for i, r in enumerate(rows):
            await self.conn.execute(
                "UPDATE cheat_sections SET sort_order=? WHERE id=?;",
                (i, int(r["id"])),
            )
        await self.conn.commit()

    async def move_section(self, section_id: int, direction: str):
        """
        direction: 'up' | 'down'
        Меняем местами sort_order с соседним разделом.
        """
        assert self.conn is not None

        cur = await self.conn.execute(
            "SELECT id, sort_order FROM cheat_sections WHERE id=?;",
            (section_id,),
        )
        row = await cur.fetchone()
        if not row:
            return

        so = int(row["sort_order"])

        if direction == "up":
            cur2 = await self.conn.execute(
                """SELECT id, sort_order FROM cheat_sections
                   WHERE sort_order < ?
                   ORDER BY sort_order DESC, id DESC
                   LIMIT 1;""",
                (so,),
            )
        else:
            cur2 = await self.conn.execute(
                """SELECT id, sort_order FROM cheat_sections
                   WHERE sort_order > ?
                   ORDER BY sort_order ASC, id ASC
                   LIMIT 1;""",
                (so,),
            )

        neigh = await cur2.fetchone()
        if not neigh:
            return

        n_id = int(neigh["id"])
        n_so = int(neigh["sort_order"])

        # swap
        await self.conn.execute("UPDATE cheat_sections SET sort_order=? WHERE id=?;", (n_so, section_id))
        await self.conn.execute("UPDATE cheat_sections SET sort_order=? WHERE id=?;", (so, n_id))
        await self.conn.commit()
