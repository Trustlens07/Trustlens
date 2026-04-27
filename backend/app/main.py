from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.middlewares.error_handler import add_exception_handlers
from app.middlewares.request_logger import RequestLoggerMiddleware
from app.middlewares.audit_logger import AuditLogMiddleware
import firebase_admin
from firebase_admin import credentials
import os
import json
import logging

if not firebase_admin._apps:
    firebase_key_json = os.environ.get("FIREBASE_KEY")
    cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    
    firebase_initialized = False
    
    # Try to initialize from FIREBASE_KEY (Cloud Run)
    if firebase_key_json:
        try:
            cred_dict = json.loads(firebase_key_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✓ Firebase initialized from Secret Manager (FIREBASE_KEY)")
            firebase_initialized = True
        except Exception as e:
            print(f"⚠️ Failed to initialize Firebase from FIREBASE_KEY: {e}")
    
    # Try to initialize from local file (local development)
    if not firebase_initialized and cred_path and os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✓ Firebase initialized from local file (development)")
            firebase_initialized = True
        except Exception as e:
            print(f"⚠️ Failed to initialize Firebase from file: {e}")
    
    if not firebase_initialized:
        print("⚠️ WARNING: Firebase not initialized. Auth endpoints will fail.")
        print("   Set FIREBASE_KEY (JSON string) or FIREBASE_SERVICE_ACCOUNT_KEY_PATH (file path)")

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "*"
    ],
    max_age=86400,
    expose_headers=["Content-Length", "Content-Range"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(AuditLogMiddleware)

# Exception handlers
add_exception_handlers(app)

# Static files for ReDoc
try:
    _STATIC_DIR = Path(__file__).resolve().parent / "static"
    _STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
except Exception as e:
    print(f"⚠️ Warning: Could not mount static files: {e}")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Handle startup - log configuration status"""
    try:
        logger.info("🚀 Starting up server...")
        
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Database URL configured: {bool(settings.DATABASE_URL)}")
        logger.info(f"Supabase URL configured: {bool(settings.SUPABASE_URL)}")
        logger.info(f"Supabase service key configured: {bool(settings.SUPABASE_SERVICE_KEY)}")
        logger.info(f"ML service URL configured: {bool(settings.ML_PARSING_SERVICE_URL)}")
        
        try:
            from app.services.storage_service import get_storage_service
            get_storage_service()
            logger.info("✅ StorageService initialized")
        except Exception as e:
            logger.warning(f"⚠️ StorageService not available: {e}")
        
        try:
            from app.services.ml_client import get_ml_client
            get_ml_client()
            logger.info("✅ MLClient initialized")
        except Exception as e:
            logger.warning(f"⚠️ MLClient not available: {e}")
        
        logger.info("✅ Application startup complete")
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR DURING STARTUP: {str(e)}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Handle graceful shutdown"""
    logger.info("⏹️ Shutting down server...")
    logger.info("✅ Shutdown complete")


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run - lightweight and fast"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check for Cloud Run"""
    try:
        if settings.DATABASE_URL:
            from app.core.database import SessionLocal, get_engine
            db_engine = get_engine()
            if db_engine is None:
                return JSONResponse(
                    status_code=503,
                    content={"status": "not ready", "reason": "database engine failed to initialize"}
                )
            SessionLocal.configure(bind=db_engine)
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {"status": "ready", "database": "connected"}
        else:
            return {"status": "ready", "database": "not configured (optional)"}
    except Exception as e:
        logger.warning(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": str(e)}
        )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )