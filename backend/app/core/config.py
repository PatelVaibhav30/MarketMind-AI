from enum import Enum
from functools import lru_cache

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Global application configuration.
    All configuration values are loaded from the .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================================
    # Application
    # ============================================================

    app_name: str = Field(
        default="MarketMind AI",
        description="Application name",
    )

    app_version: str = Field(
        default="0.1.0",
        description="Current application version",
    )

    environment: Environment = Field(
        default=Environment.DEVELOPMENT
    )

    debug: bool = Field(default=True)

    host: str = Field(default="0.0.0.0")

    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
    )

    # ============================================================
    # Database
    # ============================================================

    database_url: str = Field(
        default="",
        description="PostgreSQL connection string",
    )

    test_database_url: str = Field(
    default="",
    description="PostgreSQL connection string for automated tests",
    )

    # ============================================================
    # Redis
    # ============================================================

    redis_url: str = Field(
        default="",
        description="Redis connection string",
    )

    # ============================================================
    # AI
    # ============================================================

    openai_api_key: SecretStr | None = None

    gemini_api_key: SecretStr | None = None

    # ============================================================
    # Scheduler
    # ============================================================

    scheduler_timezone: str = "Asia/Kolkata"

    scheduler_hour: int = Field(
        default=8,
        ge=0,
        le=23,
    )

    scheduler_minute: int = Field(
        default=0,
        ge=0,
        le=59,
    )

    # ============================================================
    # Logging
    # ============================================================

    log_level: str = Field(default="INFO")

    log_directory: str = Field(default="logs")

    # ============================================================
    # Computed Properties
    # ============================================================

    @computed_field
    @property
    def base_url(self) -> str:
        protocol = "https" if self.environment == Environment.PRODUCTION else "http"
        return f"{protocol}://{self.host}:{self.port}"

    @computed_field
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()