"""
Main FastAPI application entry point for ngx-intelligence.

Configures the application, middleware, routing, and lifecycle events.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.logging import setup_logging
from app.database.session import init_db, sessionmanager
from app.schemas import HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()

    # Setup logging
    log_dir = Path("/app/logs") if not settings.app.debug else None
    setup_logging(
        log_level=settings.app.log_level,
        log_dir=log_dir,
        app_name=settings.app.name,
    )

    # Initialize database
    init_db()

    # Create tables if they don't exist
    await sessionmanager.create_all()

    # Initialize and start queue processor
    from app.workers import init_queue_processor
    from app.core.logging import get_logger

    logger = get_logger(__name__)

    queue_processor = None
    try:
        logger.info("Initializing queue processor...")
        queue_processor = init_queue_processor()
        await queue_processor.start()
        logger.info("Queue processor started successfully")
    except Exception as e:
        logger.error(f"Failed to start queue processor: {e}", exc_info=True)
        logger.warning("Application will continue without queue processor")

    yield

    # Shutdown
    # Stop queue processor
    if queue_processor:
        try:
            logger.info("Stopping queue processor...")
            await queue_processor.stop()
            logger.info("Queue processor stopped")
        except Exception as e:
            logger.error(f"Error stopping queue processor: {e}", exc_info=True)

    # Close database
    await sessionmanager.close()


# Create FastAPI application
def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="ngx-intelligence API",
        description="AI-powered document processing for Paperless-NGX",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
        redirect_slashes=False,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api")

    # Health check endpoint
    @app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
    async def health_check() -> HealthCheckResponse:
        """
        Health check endpoint.

        Returns system status and component health.
        """
        # Check database
        db_healthy = await sessionmanager.health_check()

        # Check queue processor/AI provider
        ai_healthy = True
        try:
            from app.workers import get_queue_processor
            processor = get_queue_processor()
            ai_healthy = processor.is_healthy()
        except RuntimeError:
            # Queue processor not initialized (probably disabled)
            ai_healthy = False
        except Exception as e:
            logger.error(f"Error checking queue processor health: {e}")
            ai_healthy = False

        return HealthCheckResponse(
            status="healthy" if db_healthy else "unhealthy",
            database=db_healthy,
            ai_provider=ai_healthy,
        )

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": "ngx-intelligence API",
            "version": "1.0.0",
            "docs": "/api/docs",
            "health": "/health",
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Handle uncaught exceptions."""
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.error(f"Uncaught exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.app.debug else "An error occurred",
            },
        )

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
