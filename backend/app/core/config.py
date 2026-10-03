from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    # Security
    SECRET_KEY: str = "dev-only-secret-key-change-me-in-production-0123456789"  # noqa: S105 - dev default; set SECRET_KEY in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12

    # Bootstrap administrator (created at startup if no administrator exists)
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None
    ADMIN_NAME: str = "System Administrator"

    # Business configuration
    STAFF_CAN_ASSIGN: bool = True
    SLA_CHECK_INTERVAL_SECONDS: int = 60
    ENABLE_SCHEDULER: bool = True

    # Frontend
    SERVE_FRONTEND: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
