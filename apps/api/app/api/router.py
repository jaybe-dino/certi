"""Aggregates all v1 API routes."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    compliance,
    diagnostics,
    facilities,
    health,
    onboarding,
    workspaces,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(diagnostics.router)
api_router.include_router(workspaces.router)
api_router.include_router(onboarding.router)
api_router.include_router(facilities.router)
api_router.include_router(compliance.router)

# Future feature routers (products, ...) mount here.
