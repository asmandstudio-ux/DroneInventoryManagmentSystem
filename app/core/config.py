from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "DroneInventoryManagmentSystem API"
    ENV: str = "dev"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000"

    # Security
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/droneims"

    # S3/MinIO
    S3_ENDPOINT_URL: str | None = None  # e.g. http://localhost:9000 for MinIO
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = "droneims"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_PRESIGN_EXPIRES_SECONDS: int = 900

    # Background jobs
    # - True: API runs report jobs inline via asyncio.create_task (single-process dev default)
    # - False: external worker (ai-worker) drains queued jobs from Postgres
    REPORT_JOBS_INLINE: bool = True

    # Scan processing jobs (e.g. barcode decode from uploaded evidence images)
    # - True: API runs scan jobs inline (dev default)
    # - False: external worker drains queued scan jobs from Postgres
    SCAN_JOBS_INLINE: bool = True
    # Auto-enqueue scan jobs when evidence upload is confirmed.
    SCAN_JOBS_AUTO_ENQUEUE: bool = True


settings = Settings()

