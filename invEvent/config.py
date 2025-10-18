import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    bot_token: str
    bot_username: str
    db_path: Path
    share_token_ttl_hours: int


def load_settings(env_path: Optional[Path] = None) -> Settings:
    if env_path is None:
        env_path = Path('.') / '.env'

    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise RuntimeError('BOT_TOKEN must be set in the environment')

    bot_username = os.getenv('BOT_USERNAME')
    if not bot_username:
        raise RuntimeError('BOT_USERNAME must be set in the environment')

    db_path = Path(os.getenv('DB_PATH', './inv_event.db')).expanduser().resolve()
    ttl_hours = int(os.getenv('SHARE_TOKEN_TTL_HOURS', '48'))

    return Settings(
        bot_token=bot_token,
        bot_username=bot_username,
        db_path=db_path,
        share_token_ttl_hours=ttl_hours,
    )
