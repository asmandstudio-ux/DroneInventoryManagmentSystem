from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.db.session import engine


def create_app() -> FastAPI:
    if settings.ENV.lower() != "dev" and settings.JWT_SECRET_KEY == "change-me":
        raise RuntimeError("Refusing to start with default JWT_SECRET_KEY in non-dev ENV")

    app = FastAPI(title=settings.APP_NAME)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/ready")
    async def ready():
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()

