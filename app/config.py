from dataclasses import dataclass
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: set[int]
    db_path: str


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is empty. Put token into .env")

    admin_raw = os.getenv("ADMIN_IDS", "").strip()
    admin_ids: set[int] = set()
    if admin_raw:
        for part in admin_raw.split(","):
            part = part.strip()
            if part:
                admin_ids.add(int(part))

    db_path = os.getenv("DB_PATH", "bot.db").strip() or "bot.db"

    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        db_path=db_path,
    )
