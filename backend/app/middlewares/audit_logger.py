"""Audit logging middleware for compliance and security tracking."""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

# Setup audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs
audit_handler = logging.FileHandler("audit.log")
audit_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(message)s')  # JSON format, no prefix
audit_handler.setFormatter(formatter)
audit_logger.addHandler(audit_handler)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses for audit purposes."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enabled = settings.AUDIT_LOG_ENABLED
    
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        start_time = time.time()
        
        # Build audit log entry
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "api_request",
            "request": {
                "method": request.method,
                "path": str(request.url.path),
                "query_params": str(request.url.query),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        }
        
        # Get user info if available
        user_info = await self._get_user_info(request)
        if user_info:
            audit_entry["user"] = user_info
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add response info
            duration_ms = round((time.time() - start_time) * 1000, 2)
            audit_entry["response"] = {
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
            
            # Determine if this is a sensitive operation
            if self._is_sensitive_operation(request):
                audit_entry["event_type"] = "sensitive_operation"
                audit_entry["sensitivity"] = self._get_sensitivity_level(request)
            
            # Log based on severity
            if response.status_code >= 400:
                audit_entry["severity"] = "warning" if response.status_code < 500 else "error"
                audit_logger.warning(json.dumps(audit_entry))
            else:
                audit_entry["severity"] = "info"
                audit_logger.info(json.dumps(audit_entry))
            
            return response
            
        except Exception as e:
            # Log exception
            audit_entry["response"] = {
                "status_code": 500,
                "error": str(e),
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            }
            audit_entry["severity"] = "critical"
            audit_logger.error(json.dumps(audit_entry))
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _get_user_info(self, request: Request) -> Optional[dict]:
        """Extract user info from request state if authenticated."""
        try:
            # Check for Firebase auth user
            if hasattr(request.state, "user") and request.state.user:
                user = request.state.user
                return {
                    "uid": user.get("uid"),
                    "email": user.get("email"),
                    "auth_provider": "firebase"
                }
        except:
            pass
        
        # Try to get from Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return {"auth_method": "bearer_token", "token_prefix": auth_header[:20] + "..."}
        
        return None
    
    def _is_sensitive_operation(self, request: Request) -> bool:
        """Determine if this is a sensitive operation requiring audit."""
        sensitive_paths = [
            "/auth",
            "/upload",
            "/screening",
            "/candidates",
            "/bias/analyze",
            "/scores",
        ]
        
        path = request.url.path
        method = request.method
        
        # Write operations on sensitive paths
        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            for sensitive in sensitive_paths:
                if sensitive in path:
                    return True
        
        # Read operations on bias/scoring
        if "bias" in path or "score" in path:
            return True
        
        return False
    
    def _get_sensitivity_level(self, request: Request) -> str:
        """Determine sensitivity level of the operation."""
        path = request.url.path
        method = request.method
        
        # High sensitivity: Deletions, bias analysis affecting candidates
        if method == "DELETE":
            return "high"
        
        if "/bias/analyze" in path or "/screening" in path:
            return "high"
        
        # Medium sensitivity: Uploads, scoring
        if "/upload" in path or "/scores" in path:
            return "medium"
        
        # Low: General reads
        return "low"


class AuditLogger:
    """Manual audit logging utility for business events."""
    
    @staticmethod
    def log_candidate_screening(
        candidate_id: str,
        session_id: str,
        score: float,
        user_id: Optional[str] = None,
        bias_detected: bool = False
    ):
        """Log candidate screening event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "candidate_screening",
            "candidate_id": candidate_id,
            "session_id": session_id,
            "score": score,
            "bias_detected": bias_detected,
            "user_id": user_id,
            "severity": "high" if bias_detected else "medium"
        }
        audit_logger.info(json.dumps(entry))
    
    @staticmethod
    def log_decision(
        application_id: str,
        candidate_id: str,
        decision: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log hiring decision event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "hiring_decision",
            "application_id": application_id,
            "candidate_id": candidate_id,
            "decision": decision,
            "user_id": user_id,
            "reason": reason,
            "severity": "high"
        }
        audit_logger.info(json.dumps(entry))
    
    @staticmethod
    def log_bias_alert(
        session_id: str,
        metric_type: str,
        severity: str,
        affected_groups: list,
        recommendation: str
    ):
        """Log bias detection alert."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "bias_alert",
            "session_id": session_id,
            "metric_type": metric_type,
            "severity": severity,
            "affected_groups": affected_groups,
            "recommendation": recommendation,
        }
        audit_logger.warning(json.dumps(entry))
    
    @staticmethod
    def log_data_export(
        user_id: str,
        export_type: str,
        filters: dict,
        record_count: int
    ):
        """Log data export event for GDPR/compliance."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "data_export",
            "user_id": user_id,
            "export_type": export_type,
            "filters": filters,
            "record_count": record_count,
            "severity": "medium"
        }
        audit_logger.info(json.dumps(entry))
