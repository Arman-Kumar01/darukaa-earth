"""Darukaa.Earth Backend Application Entry Point."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Darukaa.Earth API",
        description=(
            "Geospatial Carbon & Biodiversity Project Intelligence Platform API.\n\n"
            "**Demo Notice**: Analytics data uses synthetic datasets for demonstration purposes "
            "and does not represent actual environmental measurements."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(api_router, prefix="/api")

    @application.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Health check endpoint for deployment verification."""
        return {"status": "ok", "version": "1.0.0", "service": "darukaa-earth-api"}

    @application.on_event("startup")
    async def startup_event() -> None:
        logger.info("Darukaa.Earth API starting up...")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"CORS origins: {settings.cors_origins_list}")

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        logger.info("Darukaa.Earth API shutting down...")

    return application


app = create_application()
