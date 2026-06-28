"""
FastAPI application entry point.
Sets up CORS, middleware, and routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import get_settings
from app.api.v1.router import api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("dsr_platform")

# OCR engine singleton — preloaded on startup
ocr_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events."""
    global ocr_engine

    logger.info("🚀 Starting DSR Petrol Platform...")

    # Preload PaddleOCR model (takes a few seconds on first load)
    try:
        from app.ocr.engine import OCREngine
        ocr_engine = OCREngine()
        logger.info("✅ PaddleOCR engine loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ PaddleOCR failed to load: {e}. OCR will initialize on first request.")

    logger.info("✅ DSR Petrol Platform started successfully")
    yield

    logger.info("👋 Shutting down DSR Petrol Platform...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="Petroleum Pump DSR OCR, Sales Management & Analytics Platform",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        return response

    # Health check
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.APP_ENV,
        }

    # Mount API routes
    app.include_router(api_v1_router, prefix="/api/v1")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."}
        )

    return app


app = create_app()


def get_ocr_engine():
    """Get the preloaded OCR engine."""
    global ocr_engine
    if ocr_engine is None:
        from app.ocr.engine import OCREngine
        ocr_engine = OCREngine()
    return ocr_engine


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development
    )
