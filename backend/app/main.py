from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.knowledge_admin import router as knowledge_admin_router
from backend.app.api.routes.operations import router as operations_router
from backend.app.api.routes.support import router as support_router
from backend.app.core.config import Settings, get_settings
from backend.app.observability import begin_correlation, correlation_id_var, telemetry


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Backend API for the Telecom Agentic AI Support Platform",
        version="0.1.0",
        debug=settings.app_debug,
    )

    app.state.settings = settings
    app.state.is_ready = True

    @app.middleware("http")
    async def correlation_middleware(request, call_next):
        supplied = request.headers.get("X-Correlation-ID")
        safe_id = supplied if supplied and len(supplied) <= 100 else None
        token = begin_correlation(safe_id)
        from time import perf_counter

        started = perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id_var.get()
            telemetry.record(
                "http.request",
                started=started,
                method=request.method,
                route=request.url.path,
                status=response.status_code,
            )
            return response
        except Exception:
            telemetry.record(
                "http.request", started=started, outcome="error", error="internal_error"
            )
            raise
        finally:
            correlation_id_var.reset(token)

    # Allow requests only from configured frontend origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(knowledge_admin_router)
    app.include_router(support_router)
    app.include_router(operations_router)

    return app


app = create_app()
