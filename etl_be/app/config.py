from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_queue: str = os.getenv("RABBITMQ_QUEUE", "orders_raw")
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "guest")

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "orders_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "orders_pass")
    postgres_db: str = os.getenv("POSTGRES_DB", "orders_db")

    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "upload")).resolve()
    migrate_on_start: bool = os.getenv("MIGRATE_ON_START", "true").lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings

