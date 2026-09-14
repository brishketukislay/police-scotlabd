from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Configuration is environment-driven so the same application can run
    locally, in test, staging and production without code changes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Digital Youth Platform"
    app_version: str = "2.0.0"

    app_env: str = Field(
        default="development",
        description="development, test, staging or production",
    )

    debug: bool = False

    # Database
    database_url: str = "sqlite:///./youth_platform.db"
    database_echo: bool = False

    # Authentication / sessions
    session_secret: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        min_length=16,
    )

    session_cookie_name: str = "dyp_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 7
    session_cookie_secure: bool = False
    session_cookie_http_only: bool = True
    session_cookie_same_site: str = "lax"

    # Frontend / CORS
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
        ]
    )

    frontend_dist_path: str = "frontend/dist"

    # Programme defaults
    default_target_xp: int = 1_500_000
    default_programme_duration_weeks: int = 24

    # XP safety limits
    max_manual_xp_adjustment: int = 50_000
    max_group_penalty_xp: int = 150_000
    max_xp_multiplier: float = 2.0

    # Public leaderboard
    public_leaderboard_enabled: bool = True
    public_leaderboard_poll_seconds: int = 15

    # Notifications
    notifications_enabled: bool = True
    browser_notifications_enabled: bool = True

    # Community awards
    community_awards_enabled: bool = True
    community_award_requires_staff_approval: bool = True

    # Validation
    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        value = value.strip().lower()

        allowed = {
            "development",
            "test",
            "staging",
            "production",
        }

        if value not in allowed:
            raise ValueError(
                f"APP_ENV must be one of: {', '.join(sorted(allowed))}"
            )

        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """
        Allow either a JSON/list value or a comma-separated environment value.
        """

        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return value

    @field_validator("session_cookie_same_site")
    @classmethod
    def validate_same_site(cls, value: str) -> str:
        value = value.lower()

        if value not in {"strict", "lax", "none"}:
            raise ValueError(
                "SESSION_COOKIE_SAME_SITE must be strict, lax or none"
            )

        return value

    @field_validator("default_target_xp")
    @classmethod
    def validate_target_xp(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "DEFAULT_TARGET_XP must be greater than zero"
            )

        return value

    @field_validator("default_programme_duration_weeks")
    @classmethod
    def validate_duration(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "DEFAULT_PROGRAMME_DURATION_WEEKS must be greater than zero"
            )

        return value

    @field_validator("max_xp_multiplier")
    @classmethod
    def validate_multiplier(cls, value: float) -> float:
        if value < 1:
            raise ValueError(
                "MAX_XP_MULTIPLIER cannot be less than 1"
            )

        return value

    def is_production(self) -> bool:
        return self.app_env == "production"

    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings instance.
    """
    return Settings()


# Backwards-compatible module-level settings object.
#
# Existing modules currently import:
#
#     from app.core.config import settings
#
# Keeping this object means those imports continue to work while the
# dependency-friendly get_settings() accessor remains available.
settings = get_settings()
