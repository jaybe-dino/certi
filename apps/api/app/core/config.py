"""Application settings loaded from environment / .env file."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    # Accepts a JSON array OR a comma-separated string (handy on PaaS dashboards):
    #   BACKEND_CORS_ORIGINS=https://app.vercel.app,https://www.example.com
    backend_cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> object:
        # NoDecode keeps the raw env string here; accept JSON array or CSV.
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                import json

                return json.loads(s)
            return [o.strip() for o in s.split(",") if o.strip()]
        return v

    # ── FDA ESG NextGen API ──────────────────────────────────
    esg_base_url: str | None = None
    esg_api_key: str | None = None
    esg_env: str = "test"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        """Async SQLAlchemy URL — explicit DATABASE_URL wins, else built from parts.

        Normalizes the scheme to ``postgresql+asyncpg`` so a platform-provided
        ``postgresql://`` / ``postgres://`` URL (e.g. Railway, Render, Heroku)
        works without manual editing, and strips the psycopg-style ``sslmode``
        query param which asyncpg does not understand.
        """
        if self.database_url:
            return _normalize_async_dsn(self.database_url)
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


def _normalize_async_dsn(url: str) -> str:
    """Coerce a Postgres URL to the asyncpg driver and drop sslmode."""
    from urllib.parse import urlsplit, urlunsplit

    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    elif scheme.startswith("postgres") and "+psycopg" in scheme:
        scheme = "postgresql+asyncpg"

    # Remove sslmode=... (psycopg-only); keep any other query params.
    query = "&".join(
        kv for kv in parts.query.split("&") if kv and not kv.startswith("sslmode=")
    )
    return urlunsplit((scheme, parts.netloc, parts.path, query, parts.fragment))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
