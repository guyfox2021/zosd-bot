import sqlite3


USER_ID = 399453320
DB_PATH = "/root/zosd-bot/bot.db"


with sqlite3.connect(DB_PATH) as conn:
    rows = conn.execute(
        """
        SELECT password, used, used_at
        FROM access_passwords
        WHERE used_by_user_id = ?
        ORDER BY id
        """,
        (USER_ID,),
    ).fetchall()
    print(
        "authorized=",
        conn.execute(
            "SELECT COUNT(*) FROM authorized_users WHERE user_id = ?",
            (USER_ID,),
        ).fetchone()[0],
        sep="",
    )
    print("unused=", conn.execute("SELECT COUNT(*) FROM access_passwords WHERE used = 0").fetchone()[0], sep="")
    print("used_by_user_count=", len(rows), sep="")
    for password, used, used_at in rows:
        print(f"{password} | used={used} | used_at={used_at}")
