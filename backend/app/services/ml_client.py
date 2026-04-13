import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib.parse import urlparse
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

class MLClient:
    def __init__(self):
        self.timeout = 90.0
        # Use AsyncClient for async methods (prevents blocking)
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def parse_resume(self, file_url: str) -> Dict[str, Any]:
        """Call ML parsing service (multipart/form-data with `file`)."""
        try:
            # Download bytes using a fresh signed URL if this is a Supabase public URL.
            signed_url = file_url
            parsed = urlparse(file_url)
            path = parsed.path or ""
            bucket = settings.STORAGE_BUCKET_NAME
            public_marker = f"/storage/v1/object/public/{bucket}/"
            sign_marker = f"/storage/v1/object/sign/{bucket}/"
            object_key = None
            if public_marker in path:
                object_key = path.split(public_marker, 1)[1].lstrip("/")
            elif sign_marker in path:
                object_key = path.split(sign_marker, 1)[1].lstrip("/")

            if object_key:
                candidate_keys = [object_key]
                if object_key.startswith(f"{bucket}/"):
                    candidate_keys.append(object_key[len(bucket) + 1 :])
                for key in candidate_keys:
                    try:
                        signed_url = storage_service.get_file_url(key)
                        break
                    except Exception:
                        continue

            # Use async client for GET
            file_resp = await self.client.get(signed_url)
            file_resp.raise_for_status()
            file_bytes = file_resp.content
            filename = parsed.path.rsplit("/", 1)[-1] or "resume"
            content_type = file_resp.headers.get("content-type") or "application/octet-stream"

            # POST with files (multipart)
            response = await self.client.post(
                f"{settings.ML_PARSING_SERVICE_URL}/parse",
                files={"file": (filename, file_bytes, content_type)},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ML parsing failed: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def score_resume(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call ML scoring service with correct resume.file_name field."""
        try:
            # Extract the actual resume data (sometimes wrapped under 'parsed_data')
            inner_data = parsed_data.get("parsed_data", parsed_data)
            
            # Extract file_name – try multiple possible locations
            file_name = (
                inner_data.get("file_name") or
                parsed_data.get("file_name") or
                "resume.pdf"
            )
            
            # Extract required skills (list of skill names)
            skills = inner_data.get("skills") or []
            required_skills = [s.get("name") for s in skills if isinstance(s, dict) and s.get("name")]
            
            # Extract resume text (if available, otherwise empty string)
            resume_text = (
                inner_data.get("text_preview") or
                inner_data.get("text") or
                parsed_data.get("text_preview", "")
            )
            
            # Build payload exactly as ML service expects
            payload = {
                "required_skills": required_skills,
                "resume": {
                    "file_name": file_name,
                    "text": resume_text,
                    "parsed_data": inner_data   # full parsed content
                }
            }
            
            logger.info(f"Sending scoring request for file: {file_name}")
            response = await self.client.post(
                f"{settings.ML_SCORING_SERVICE_URL}/score",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Scoring successful for {file_name}")
            return result
        except Exception as e:
            logger.error(f"ML scoring failed: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def enhance_resume(
        self,
        resume_text: str,
        original_score: float,
        original_breakdown: Dict[str, Any],
        original_bias_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call ML enhance service to get Gemini-enhanced score."""
        try:
            payload = {
                "resume_text": resume_text,
                "original_score": original_score,
                "original_breakdown": original_breakdown,
                "original_bias_metrics": original_bias_metrics or {}
            }
            response = await self.client.post(
                f"{settings.ML_ENHANCE_SERVICE_URL}/enhance",
                json=payload,
                timeout=20.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ML enhance service failed: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_bias(self, candidates_data: list, scores: list[float]) -> Dict[str, Any]:
        """Call ML bias analysis service"""
        try:
            response = await self.client.post(
                f"{settings.ML_BIAS_SERVICE_URL}/bias/detect",
                json={"candidates_data": candidates_data, "scores": scores}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ML bias analysis failed: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_feedback(self, score_data: Dict[str, Any], parsed_data: Dict[str, Any]) -> str:
        """Call ML feedback service"""
        try:
            response = await self.client.post(
                f"{settings.ML_FEEDBACK_SERVICE_URL}/generate",
                json={
                    "score_data": score_data,
                    "parsed_data": parsed_data
                }
            )
            response.raise_for_status()
            return response.json().get("feedback", "")
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 404:
                return ""
            logger.error(f"ML feedback generation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"ML feedback generation failed: {str(e)}")
            raise
    
    async def close(self):
        """Close the HTTP client gracefully."""
        await self.client.aclose()

# Singleton instance
ml_client = MLClient()