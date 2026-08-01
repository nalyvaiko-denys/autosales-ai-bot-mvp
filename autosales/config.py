from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _integer_list(value: str) -> list[int]:
    result: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            parsed = int(item)
        except ValueError:
            continue
        if parsed not in result:
            result.append(parsed)
    return result


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AutoSales AI Bot"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://autosales:autosales@postgres:5432/autosales"
    redis_url: str = "redis://redis:6379/0"
    create_tables_on_start: bool = False

    telegram_bot_token: SecretStr | None = None
    manager_chat_ids: str = ""
    telegram_admin_ids: str = ""
    sales_phone_1: str = "+380440000001"
    sales_phone_2: str = "+380440000002"

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.6-luna"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_timeout_seconds: float = 10.0
    openai_max_retries: int = 2
    embedding_dimensions: int = 1536

    staff_api_token: SecretStr = SecretStr("change-me-in-production")
    admin_username: str = "admin"
    admin_password: SecretStr = SecretStr("change-me-in-production")
    session_secret: SecretStr = SecretStr("change-me-session-secret")
    public_base_url: str = "http://localhost:8000"

    @field_validator("database_url")
    @classmethod
    def normalize_postgres_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def manager_chat_id_list(self) -> list[int]:
        return _integer_list(self.manager_chat_ids)

    @property
    def manager_chat_username_list(self) -> list[str]:
        return list(
            dict.fromkeys(
                item.strip().removeprefix("@").lower()
                for item in self.manager_chat_ids.split(",")
                if item.strip().startswith("@") and len(item.strip()) > 1
            )
        )

    @property
    def telegram_admin_id_list(self) -> list[int]:
        return _integer_list(self.telegram_admin_ids)

    def is_telegram_admin(self, user_id: int) -> bool:
        return user_id in self.telegram_admin_id_list

    @property
    def sales_phone_list(self) -> list[str]:
        return [phone for phone in (self.sales_phone_1, self.sales_phone_2) if phone]

    @property
    def has_openai(self) -> bool:
        return self.openai_api_key is not None and bool(self.openai_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()
