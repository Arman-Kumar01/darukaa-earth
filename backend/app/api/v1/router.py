"""Main API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import analytics, auth, dashboard, map_endpoints, projects, sites

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(sites.router, prefix="/sites", tags=["Sites"])
api_router.include_router(analytics.router, prefix="", tags=["Analytics"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(map_endpoints.router, prefix="/map", tags=["Map"])
