from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        self.db_host = self._require("DB_HOST")
        self.db_port = int(self._require("DB_PORT"))
        self.db_name = self._require("DB_NAME")
        self.db_user = self._require("DB_USER")
        self.db_password = self._require("DB_PASSWORD")
        self.frontend_origins = self._csv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        self.auth_secret_key = self._optional("AUTH_SECRET_KEY") or secrets.token_urlsafe(48)
        self.auth_session_seconds = int(self._optional("AUTH_SESSION_SECONDS") or 8 * 60 * 60)
        self.auth_cookie_secure = self._bool("AUTH_COOKIE_SECURE", False)
        self.auth_cookie_samesite = self._optional("AUTH_COOKIE_SAMESITE") or "lax"

    @staticmethod
    def _require(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

    @staticmethod
    def _optional(name: str) -> str | None:
        value = os.getenv(name)
        return value.strip() if value and value.strip() else None

    @classmethod
    def _csv(cls, name: str, default: str) -> list[str]:
        raw_value = cls._optional(name) or default
        return [item.strip() for item in raw_value.split(",") if item.strip()]

    @classmethod
    def _bool(cls, name: str, default: bool) -> bool:
        value = cls._optional(name)
        if value is None:
            return default
        return value.lower() in {"1", "true", "yes", "on"}

    @property
    def sqlalchemy_database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


settings = Settings()
