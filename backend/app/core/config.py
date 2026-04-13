from typing import List
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
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Storage
    STORAGE_BUCKET_NAME: str = os.getenv("STORAGE_BUCKET_NAME", "resumes")
    STORAGE_URL_EXPIRY: int = int(os.getenv("STORAGE_URL_EXPIRY", "3600"))
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx"]
    
    # ML Services
    ML_PARSING_SERVICE_URL: str = os.getenv("ML_PARSING_SERVICE_URL", "http://localhost:8001")
    ML_SCORING_SERVICE_URL: str = os.getenv("ML_SCORING_SERVICE_URL", "http://localhost:8002")
    ML_BIAS_SERVICE_URL: str = os.getenv("ML_BIAS_SERVICE_URL", "http://localhost:8003")
    ML_FEEDBACK_SERVICE_URL: str = os.getenv("ML_FEEDBACK_SERVICE_URL", "http://localhost:8004")
    ML_ENHANCE_SERVICE_URL: str = os.getenv("ML_ENHANCE_SERVICE_URL", "http://localhost:8005")
    
    # API Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
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