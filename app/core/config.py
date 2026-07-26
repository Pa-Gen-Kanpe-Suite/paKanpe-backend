from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PA GEN KANPE API"
    environment: str = "development"
    database_url: str = "sqlite:///./pagenkanpe.db"
    jwt_secret: str = "development-only-secret-change-me-123456789"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    frontend_origins: str = "http://localhost:3000"
    no_show_grace_seconds: int = 300
    default_service_minutes: int = 5
    upcoming_notification_minutes: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET doit contenir au moins 32 caractères")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
