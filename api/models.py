"""Typed response models for the operational API endpoints."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Process or dependency readiness status."""

    status: Literal["ok", "ready", "not_ready"]


class VersionResponse(BaseModel):
    """Stable application identity returned to clients and operators."""

    name: str
    version: str
    api_version: str
