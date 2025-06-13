from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.api.endpoints import router
from app.utils.logging import setup_logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)
# Test comment to trigger reload - second test

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 50)
    logger.info("SMS Service Starting...")
    logger.info(f"SMS Sending: {'Enabled' if settings.enable_sms_sending else 'Disabled'}")
    logger.info(f"Signature Validation: {'Enabled' if settings.validate_twilio_signature else 'Disabled'}")
    logger.info(f"Twilio Phone: {settings.twilio_phone_number}")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("SMS Service shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )