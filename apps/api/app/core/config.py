"""Application settings loaded from environment / .env file."""

from functools import lru_cache

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "MoCRA Compliance Platform API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"

    # ── Database ─────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "certi"
    postgres_password: str = "certi"
    postgres_db: str = "certi"
    database_url: str | None = None

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Auth ─────────────────────────────────────────────────
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    algorithm: str = "HS256"

    # ── CORS ─────────────────────────────────────────────────
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # ── FDA ESG NextGen API ──────────────────────────────────
    esg_base_url: str | None = None
    esg_api_key: str | None = None
    esg_env: str = "test"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        """Async SQLAlchemy URL — explicit DATABASE_URL wins, else built from parts."""
        if self.database_url:
            return self.database_url
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
