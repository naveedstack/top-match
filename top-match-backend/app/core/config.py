import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Top Match Backend"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = []
    PUBLIC_APP_URL: str = "http://localhost:3000"

    DATABASE_URL: PostgresDsn
    GEMINI_API_KEY: SecretStr

    JWT_SECRET: SecretStr
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7

    GEMINI_MODEL: str = "gemini-3.8-flash"
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_ATTEMPTS: int = 3
    LLM_MAX_CONCURRENCY: int = 2
    STUCK_APPLICATION_MINUTES: int = 5
    PIPELINE_ENABLED: bool = True
    RESUME_TOKEN_MINUTES: int = 15
    RETENTION_DAYS: int = 30
    GEMINI_DATA_USE_ACKNOWLEDGED: bool = False

    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_DIR: Path = Path("var/resumes")
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    S3_PREFIX: str = ""
    S3_UPLOAD_URL_SECONDS: int = 600
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: SecretStr | None = None
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024
    MAX_RESUME_PAGES: int = 5
    OCR_DPI: int = 150
    OCR_MAX_PAGE_PIXELS: int = 4_000_000

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def use_asyncpg_driver(cls, value: object) -> object:
        # asyncpg needs the explicit driver scheme and takes `ssl`, not libpq's `sslmode`.
        if isinstance(value, str):
            value = re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", value)
            value = re.sub(r"([?&])sslmode=", r"\1ssl=", value)
        return value

    @model_validator(mode="after")
    def require_s3_bucket(self) -> Settings:
        if self.STORAGE_BACKEND == "s3" and not self.S3_BUCKET.strip():
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND is s3")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
