from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.middlewares.error_handler import add_exception_handlers
from app.middlewares.request_logger import RequestLoggerMiddleware

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(RequestLoggerMiddleware)

# Add exception handlers
add_exception_handlers(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

from datetime import datetime

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    }

@app.get("/ready")
async def readiness_check():
    # Check database connection
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not ready"}
