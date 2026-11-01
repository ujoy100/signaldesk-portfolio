from fastapi import APIRouter, Request, Response, status

from backend.app.schemas.health import (
    HealthResponse,
    ReadinessResponse,
)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Check whether the API process is responding."""
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(
    request: Request,
    response: Response,
) -> ReadinessResponse:
    """Check whether the application is ready for requests."""

    is_application_ready = request.app.state.is_ready

    checks = {"application": "ok" if is_application_ready else "not_ready"}

    is_ready = all(value == "ok" for value in checks.values())

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="not_ready",
            checks=checks,
        )

    return ReadinessResponse(
        status="ready",
        checks=checks,
    )
