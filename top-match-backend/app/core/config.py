import re
from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Top Match Backend"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = []

    DATABASE_URL: PostgresDsn
    GEMINI_API_KEY: SecretStr

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def use_asyncpg_driver(cls, value: object) -> object:
        # asyncpg needs the explicit driver scheme and takes `ssl`, not libpq's `sslmode`.
        if isinstance(value, str):
            value = re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", value)
            value = re.sub(r"([?&])sslmode=", r"\1ssl=", value)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
