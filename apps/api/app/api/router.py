"""Aggregates all v1 API routes."""

from fastapi import APIRouter

from app.api.routes import auth, diagnostics, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(diagnostics.router)

# Future feature routers (facilities, products, ...) mount here.
