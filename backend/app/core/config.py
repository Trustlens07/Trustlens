from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Resume Screening Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Port (Cloud Run uses PORT env var, defaults to 8000 for local dev)
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # Supabase – Optional
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Database – Optional
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Storage
    STORAGE_BUCKET_NAME: str = os.getenv("STORAGE_BUCKET_NAME", "resumes")
    STORAGE_URL_EXPIRY: int = int(os.getenv("STORAGE_URL_EXPIRY", "3600"))
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx"]
    
    # ML Services – Optional
    ML_PARSING_SERVICE_URL: Optional[str] = os.getenv("ML_PARSING_SERVICE_URL")
    ML_SCORING_SERVICE_URL: Optional[str] = os.getenv("ML_SCORING_SERVICE_URL")
    ML_BIAS_SERVICE_URL: Optional[str] = os.getenv("ML_BIAS_SERVICE_URL")
    ML_FEEDBACK_SERVICE_URL: Optional[str] = os.getenv("ML_FEEDBACK_SERVICE_URL")
    ML_ENHANCE_SERVICE_URL: Optional[str] = os.getenv("ML_ENHANCE_SERVICE_URL")
    
    # API Configuration
    CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3003,http://localhost:3007,http://localhost:5173,http://localhost:8000"
        ).split(",")
        if origin.strip()
    ]
    # Security - Allowed Hosts
    # Default secure configuration - no wildcard in production
    ALLOWED_HOSTS: List[str] = [
        host.strip()
        for host in os.getenv(
            "ALLOWED_HOSTS",
            "localhost,127.0.0.1,*.localhost,*.run.app"  # Cloud Run default
        ).split(",")
        if host.strip() and host.strip() != "*"  # Block wildcard in production
    ] if ENVIRONMENT == "production" else ["*"]
    
    # Redis Cache
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "1800"))  # 30 min default
    
    # Audit Logging
    AUDIT_LOG_ENABLED: bool = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

settings = Settings()