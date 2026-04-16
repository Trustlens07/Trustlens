import uvicorn
import os
from app.core.config import settings

if __name__ == "__main__":
    # Use PORT environment variable (Cloud Run sets this to 8080)
    # Falls back to 8000 for local development
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )