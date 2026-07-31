import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from autosales.admin import mount_admin
from autosales.ai.provider import build_provider
from autosales.api.routers import ai, appointments, cars, crm, customers, favorites, health
from autosales.config import Settings, get_settings
from autosales.db import create_schema, engine
from autosales.errors import ConflictError, DomainError, NotFoundError
from autosales.logging import configure_logging


def create_app(
    settings: Settings | None = None, target_engine: AsyncEngine | None = None
) -> FastAPI:
    settings = settings or get_settings()
    target_engine = target_engine or engine
    configure_logging(settings.log_level)
    log = structlog.get_logger()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.ai_provider = build_provider(settings)
        if settings.create_tables_on_start:
            await create_schema(target_engine)
        log.info("application_started", environment=settings.environment)
        yield
        await target_engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Async Telegram sales automation, CRM, catalog, and grounded AI search.",
        lifespan=lifespan,
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.state.ai_provider = build_provider(settings)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            raise
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        if isinstance(exc, NotFoundError):
            code = 404
        elif isinstance(exc, ConflictError):
            code = 409
        else:
            code = 400
        return JSONResponse(status_code=code, content={"detail": str(exc)})

    for router in (
        health.router,
        customers.router,
        cars.router,
        favorites.router,
        appointments.router,
        crm.router,
        ai.router,
    ):
        app.include_router(router, prefix="/api/v1")
    mount_admin(app, target_engine, settings)
    return app


app = create_app()


def run_api() -> None:
    uvicorn.run("autosales.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run_api()
