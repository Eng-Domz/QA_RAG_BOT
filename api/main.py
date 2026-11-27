"""FastAPI application factory and operational endpoints."""

from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status

from api.models import HealthResponse, VersionResponse

APP_NAME = "Bilingual Knowledge Platform API"
APP_VERSION = "0.1.0"
API_VERSION = "v1"

ReadinessCheck = Callable[[], bool]


def create_app(readiness_check: ReadinessCheck | None = None) -> FastAPI:
    """Create an API instance without initializing the RAG or provider stack."""

    check_dependencies = readiness_check or (lambda: True)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.ready = True
        try:
            yield
        finally:
            application.state.ready = False

    application = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=(
            "Operational API boundary for the bilingual grounded-knowledge "
            "platform. Document and question endpoints are added incrementally."
        ),
        lifespan=lifespan,
    )
    application.state.ready = False

    @application.get(
        "/healthz",
        response_model=HealthResponse,
        tags=["operations"],
        summary="Check process health",
    )
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.get(
        "/readyz",
        response_model=HealthResponse,
        responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
        tags=["operations"],
        summary="Check application readiness",
    )
    def readiness(response: Response) -> HealthResponse:
        try:
            ready = bool(application.state.ready and check_dependencies())
        except Exception:
            ready = False

        if not ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return HealthResponse(status="not_ready")

        return HealthResponse(status="ready")

    @application.get(
        "/api/v1/version",
        response_model=VersionResponse,
        tags=["operations"],
        summary="Get application version",
    )
    def version() -> VersionResponse:
        return VersionResponse(
            name=APP_NAME,
            version=APP_VERSION,
            api_version=API_VERSION,
        )

    return application


app = create_app()
