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
        if self.conn is None:
            await self.connect()

        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                first_seen_at TEXT DEFAULT (datetime('now'))
            );"""
        )

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

        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM cheat_sections;")
        row = await cur.fetchone()
        if row["c"] == 0:
            await self.conn.execute("INSERT INTO cheat_sections(title, sort_order) VALUES (?, ?);", ("Приклад розділу", 0))
            cur2 = await self.conn.execute("SELECT id FROM cheat_sections LIMIT 1;")
            sec = await cur2.fetchone()
            await self.conn.execute(
                "INSERT INTO cheat_items(section_id, title, content, sort_order) VALUES (?,?,?,?);",
                (sec["id"], "Приклад пункту", "Тут буде текст шпаргалки.", 0),
            )
            await self.conn.commit()

        await self.normalize_section_orders()
        for s in await self.list_sections():
            await self.normalize_item_orders(int(s["id"]))

    async def upsert_user(self, user_id: int):
        assert self.conn is not None
        await self.conn.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?);", (user_id,))
        await self.conn.commit()

    async def list_users(self) -> list[int]:
        assert self.conn is not None
        cur = await self.conn.execute("SELECT user_id FROM users;")
        rows = await cur.fetchall()
        return [int(r["user_id"]) for r in rows]

    async def create_ticket(self, user_id: int, text: str) -> int:
        assert self.conn is not None
        cur = await self.conn.execute("INSERT INTO tickets(user_id, text) VALUES(?, ?);", (user_id, text))
        await self.conn.commit()
        return int(cur.lastrowid)

    async def get_ticket(self, ticket_id: int):
        assert self.conn is not None
        cur = await self.conn.execute("SELECT * FROM tickets WHERE id = ?;", (ticket_id,))
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

    async def list_sections(self):
        assert self.conn is not None
        cur = await self.conn.execute("SELECT * FROM cheat_sections ORDER BY sort_order, id;")
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
        cur = await self.conn.execute("SELECT * FROM cheat_items WHERE id=?;", (item_id,))
        return await cur.fetchone()

    async def create_section(self, title: str):
        assert self.conn is not None
        cur = await self.conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS n FROM cheat_sections;")
        row = await cur.fetchone()
        await self.conn.execute("INSERT INTO cheat_sections(title, sort_order) VALUES(?, ?);", (title, int(row["n"])))
        await self.conn.commit()

    async def rename_section(self, section_id: int, title: str):
        assert self.conn is not None
        await self.conn.execute("UPDATE cheat_sections SET title=? WHERE id=?;", (title, section_id))
        await self.conn.commit()

    async def delete_section(self, section_id: int):
        assert self.conn is not None
        await self.conn.execute("DELETE FROM cheat_sections WHERE id=?;", (section_id,))
        await self.conn.commit()

    async def create_item(self, section_id: int, title: str, content: str):
        assert self.conn is not None
        cur = await self.conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 AS n FROM cheat_items WHERE section_id=?;",
            (section_id,),
        )
        row = await cur.fetchone()
        await self.conn.execute(
            "INSERT INTO cheat_items(section_id, title, content, sort_order) VALUES(?,?,?,?);",
            (section_id, title, content, int(row["n"])),
        )
        await self.conn.commit()

    async def update_item(self, item_id: int, title: str, content: str):
        assert self.conn is not None
        await self.conn.execute("UPDATE cheat_items SET title=?, content=? WHERE id=?;", (title, content, item_id))
        await self.conn.commit()

    async def delete_item(self, item_id: int):
        assert self.conn is not None
        await self.conn.execute("DELETE FROM cheat_items WHERE id=?;", (item_id,))
        await self.conn.commit()

    async def normalize_section_orders(self):
        assert self.conn is not None
        cur = await self.conn.execute("SELECT id FROM cheat_sections ORDER BY sort_order, id;")
        rows = await cur.fetchall()
        for idx, r in enumerate(rows):
            await self.conn.execute("UPDATE cheat_sections SET sort_order=? WHERE id=?;", (idx, int(r["id"])))
        await self.conn.commit()

    async def normalize_item_orders(self, section_id: int):
        assert self.conn is not None
        cur = await self.conn.execute("SELECT id FROM cheat_items WHERE section_id=? ORDER BY sort_order, id;", (section_id,))
        rows = await cur.fetchall()
        for idx, r in enumerate(rows):
            await self.conn.execute("UPDATE cheat_items SET sort_order=? WHERE id=?;", (idx, int(r["id"])))
        await self.conn.commit()

    async def move_section(self, section_id: int, direction: str):
        assert self.conn is not None
        await self.normalize_section_orders()
        cur = await self.conn.execute("SELECT id FROM cheat_sections ORDER BY sort_order, id;")
        rows = await cur.fetchall()
        ids = [int(r["id"]) for r in rows]
        if section_id not in ids:
            return
        i = ids.index(section_id)
        if direction == "up" and i > 0:
            ids[i - 1], ids[i] = ids[i], ids[i - 1]
        elif direction == "down" and i < len(ids) - 1:
            ids[i + 1], ids[i] = ids[i], ids[i + 1]
        else:
            return
        for order, sid in enumerate(ids):
            await self.conn.execute("UPDATE cheat_sections SET sort_order=? WHERE id=?;", (order, sid))
        await self.conn.commit()

    async def move_item(self, item_id: int, section_id: int, direction: str):
        assert self.conn is not None
        await self.normalize_item_orders(section_id)
        cur = await self.conn.execute("SELECT id FROM cheat_items WHERE section_id=? ORDER BY sort_order, id;", (section_id,))
        rows = await cur.fetchall()
        ids = [int(r["id"]) for r in rows]
        if item_id not in ids:
            return
        i = ids.index(item_id)
        if direction == "up" and i > 0:
            ids[i - 1], ids[i] = ids[i], ids[i - 1]
        elif direction == "down" and i < len(ids) - 1:
            ids[i + 1], ids[i] = ids[i], ids[i + 1]
        else:
            return
        for order, iid in enumerate(ids):
            await self.conn.execute("UPDATE cheat_items SET sort_order=? WHERE id=?;", (order, iid))
        await self.conn.commit()
