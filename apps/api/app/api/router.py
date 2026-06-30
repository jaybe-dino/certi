"""Aggregates all v1 API routes."""

from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)

# Future feature routers (auth, diagnostics, facilities, products, ...) mount here.
