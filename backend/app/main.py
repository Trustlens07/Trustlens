from pathlib import Path
from fastapi import FastAPI, HTTPException
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
import firebase_admin
from firebase_admin import credentials
import os


# --- Firebase Initialization (Cloud Run compatible) ---
import json

if not firebase_admin._apps:
    firebase_key_json = os.environ.get("FIREBASE_KEY")
    if firebase_key_json:
        try:
            cred_dict = json.loads(firebase_key_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized from Secret Manager (FIREBASE_KEY)")
        except Exception as e:
            print(f"Failed to initialize Firebase from FIREBASE_KEY: {e}")
            raise
    else:
        # Fallback for local development (optional)
        cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("⚠️ Firebase initialized from local file (development)")
        else:
            raise ValueError(
                "Firebase credentials not provided. Set FIREBASE_KEY (JSON string) "
                "for Cloud Run or FIREBASE_SERVICE_ACCOUNT_KEY_PATH (file path) for local dev."
            )

# Setup logging
setup_logging()

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
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(RequestLoggerMiddleware)

# Exception handlers
add_exception_handlers(app)

# Static files for ReDoc
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Include API router (only once, prefix /api/v1)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Optional: keep a simple /api alias for convenience (but may cause duplication)
# Better to remove the second include. If you really need both, use redirect.
# For now, I recommend removing: app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

from datetime import datetime, timezone

@app.get("/health")
async def health_check():
    now = datetime.now(timezone.utc)
    return {
        "status": "ok",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

@app.get("/ready")
async def readiness_check():
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not ready"}

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )