"""Centralized configuration via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_api_env = Path(__file__).resolve().parents[2] / ".env"
_root_env = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    """All runtime configuration. Reads from env."""

    model_config = SettingsConfigDict(
        env_file=(_api_env, _root_env),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core
    helix_env: str = "development"
    version: str = "0.1.0"
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key-change-me"
    encryption_key: str = "dev-encryption-key-change-me-32b"

    # Database
    database_url: str = "postgresql+asyncpg://helix:helix@postgres:5432/helix"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Storage (S3 / MinIO)
    s3_endpoint: str = "http://minio:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "helix-assets"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    # LLM providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    deepseek_api_key: str = ""
    groq_api_key: str = ""
    mistral_api_key: str = ""
    dashscope_api_key: str = ""  # Alibaba Qwen via DashScope
    xai_api_key: str = ""  # xAI Grok API key

    # Image / video providers
    replicate_api_token: str = ""
    runway_api_key: str = ""
    google_veo_api_key: str = ""

    # Deployment tools
    vercel_token: str = ""
    vercel_team_id: str = ""
    github_token: str = ""
    github_org: str = ""

    # Productivity integrations (OAuth client creds)
    canva_client_id: str = ""
    canva_client_secret: str = ""
    figma_client_id: str = ""
    figma_client_secret: str = ""
    notion_client_id: str = ""
    notion_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""

    # Browser automation
    browser_headless: bool = True
    browser_executable_path: str = ""

    # Search
    brave_api_key: str = ""

    # Workers
    generate_mock_data: bool = False

    # Stripe billing
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""
    stripe_price_pro: str = ""
    stripe_price_business: str = ""

    # Observability
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://langfuse:3001"

    # API surface
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_public_url: str = "http://localhost:8000"
    web_public_url: str = "http://localhost:3000"
    cors_origins: str = ""  # Empty -> falls back to [web_public_url]. Comma-separated list.
    cors_allow_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allow_headers: str = "Authorization,Content-Type,X-Requested-With,X-Request-ID"
    cors_expose_headers: str = "X-Request-ID"
    cors_max_age: int = 600

    # Session / cookie behaviour
    session_cookie_name: str = "helix_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days

    # External provider endpoints (overridable for testing / sovereign cloud)
    google_auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_url: str = "https://oauth2.googleapis.com/token"
    google_userinfo_url: str = "https://openidconnect.googleapis.com/v1/userinfo"
    telegram_api_base: str = "https://api.telegram.org"
    asset_placeholder_base: str = "https://placehold.co"

    # Integration verification endpoints (overridable for testing / sovereign cloud)
    slack_api_base: str = "https://slack.com/api"
    stripe_api_base: str = "https://api.stripe.com"
    sendgrid_api_base: str = "https://api.sendgrid.com"
    airtable_api_base: str = "https://api.airtable.com"
    linear_api_base: str = "https://api.linear.app"
    integration_verify_timeout_seconds: float = 8.0

    # Run queue tunables
    run_queue_key: str = "helix:run_queue"
    run_idempotency_ttl_seconds: int = 60 * 60 * 24  # 24h

    # Asset / storage tunables
    asset_presign_ttl_seconds: int = 3600
    asset_thumbnail_suffix: str = "_thumb.webp"

    # Telegram bot tunables
    telegram_history_max: int = 8
    telegram_history_ttl_seconds: int = 60 * 60 * 24
    telegram_dedup_ttl_seconds: int = 60 * 60 * 6
    telegram_message_max_chars: int = 4096
    telegram_system_prompt: str = (
        "You are Helix — a creative AI operator. Speaking via Telegram. "
        "Reply concisely (Telegram messages are short). Use plain text, no markdown."
    )

    # Pagination defaults
    page_default_limit: int = 50
    page_max_limit: int = 200

    # Paths
    skills_dir: Path = Field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[4] / "skills"
            if (Path(__file__).resolve().parents[4] / "skills").exists()
            else Path("/app/skills")
        )
    )
    design_systems_dir: Path = Field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[4] / "design-systems"
            if (Path(__file__).resolve().parents[4] / "design-systems").exists()
            else Path("/app/design-systems")
        )
    )

    # Worker pool / reliability
    worker_concurrency: int = 8
    worker_max_retries: int = 5
    worker_retry_base_seconds: float = 2.0
    worker_healthz_port: int = 9090
    worker_hot_reload: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        """Dynamic origin list. Falls back to [web_public_url] when unset.

        Never returns ["*"] — wildcard + credentials is unsafe and rejected by browsers.
        """
        explicit = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if explicit:
            # Strip any accidental wildcard
            explicit = [o for o in explicit if o != "*"]
        return explicit or [self.web_public_url.rstrip("/")]

    @property
    def cors_methods_list(self) -> list[str]:
        return [m.strip() for m in self.cors_allow_methods.split(",") if m.strip()]

    @property
    def cors_headers_list(self) -> list[str]:
        return [h.strip() for h in self.cors_allow_headers.split(",") if h.strip()]

    @property
    def cors_expose_list(self) -> list[str]:
        return [h.strip() for h in self.cors_expose_headers.split(",") if h.strip()]

    @property
    def is_production(self) -> bool:
        return self.helix_env.lower() == "production"

    def assert_production_safe(self) -> None:
        """Raise if dev defaults / unsafe settings remain in a production deployment.

        Called from the FastAPI lifespan so a misconfigured prod deploy fails fast
        instead of silently shipping with `dev-secret-key`.
        """
        if not self.is_production:
            return
        problems: list[str] = []
        if self.secret_key.startswith("dev-") or len(self.secret_key) < 32:
            problems.append("SECRET_KEY is missing or weak (must be >=32 chars, not the dev default)")
        if self.encryption_key.startswith("dev-") or len(self.encryption_key) < 32:
            problems.append("ENCRYPTION_KEY is missing or weak")
        if "*" in self.cors_origins.split(","):
            problems.append("CORS_ORIGINS contains a wildcard")
        if self.web_public_url.startswith("http://") and "localhost" not in self.web_public_url:
            problems.append("WEB_PUBLIC_URL is non-https in production")
        if self.api_public_url.startswith("http://") and "localhost" not in self.api_public_url:
            problems.append("API_PUBLIC_URL is non-https in production")
        if "helix:helix" in self.database_url:
            problems.append("DATABASE_URL contains default credentials")
        if self.s3_access_key == "minioadmin" or self.s3_secret_key == "minioadmin":
            problems.append("S3 credentials are default MinIO values")
        if self.redis_url == "redis://redis:6379/0" and "localhost" not in self.redis_url:
            problems.append("REDIS_URL is the docker-compose default")
        if problems:
            raise RuntimeError("Unsafe production config: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
