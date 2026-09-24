from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from app.api.dependencies import get_azure_client_manager
from app.api.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import (
    InvoiceProcessorException,
    custom_exception_handler,
    generic_exception_handler,
)
from app.core.logging import setup_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for setup and cleanup."""
    setup_logging(debug=settings.DEBUG)
    logger.info(
        "Starting application",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )
    yield
    # Cleanup on shutdown
    azure_client_mgr = get_azure_client_manager(settings)
    await azure_client_mgr.close()
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Application factory for FastAPI instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="FastAPI service for invoice document processing using Azure AI Document Intelligence",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    app.add_exception_handler(InvoiceProcessorException, custom_exception_handler)
    if not settings.DEBUG:
        app.add_exception_handler(Exception, generic_exception_handler)

    # Register Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
