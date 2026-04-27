import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib.parse import urlparse
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

# Single base URL — all ML endpoints are on the same service
ML_BASE_URL = settings.ML_PARSING_SERVICE_URL or ""  # e.g. https://preeee-276-ml-service-api.hf.space


def _build_parsed_resume(parsed_data: Dict[str, Any], file_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert our stored parsed_data into the ParsedResume schema the ML service expects.

    Our storage wraps the ML response like:
    {
        "parsed_data": { <actual ParsedResume fields> },
        "mode": "baseline",
        "full_text": "...",
        ...
    }
    The ML service wants the inner ParsedResume object directly.
    """
    inner = parsed_data.get("parsed_data", parsed_data)

    # Ensure file_name is set - ML service requires this field
    # Try multiple sources: explicit param, inner data, or default
    resolved_file_name = file_name or inner.get("file_name") or parsed_data.get("file_name") or "resume.pdf"

    # Normalise skills: ML service expects [{"name": str, "category": str, "proficiency": str}]
    raw_skills = inner.get("skills", [])
    normalised_skills = []
    for s in raw_skills:
        if isinstance(s, dict):
            normalised_skills.append({
                "name": s.get("name", ""),
                "category": s.get("category", "other"),
                "proficiency": s.get("proficiency", "intermediate"),
            })
        elif isinstance(s, str):
            # Handle comma-separated skill strings
            for part in s.split(","):
                part = part.strip()
                if part:
                    normalised_skills.append({
                        "name": part,
                        "category": "other",
                        "proficiency": "intermediate",
                    })

    # Normalise experience entries
    raw_exp = inner.get("experience", [])
    normalised_exp = []
    for e in raw_exp:
        if isinstance(e, dict):
            # Ensure duration_years is a float as required by ML service
            duration = e.get("duration_years", 0.0)
            try:
                duration_float = float(duration) if duration is not None else 0.0
            except (ValueError, TypeError):
                duration_float = 0.0

            normalised_exp.append({
                "title": e.get("title", ""),
                "company": e.get("company", ""),
                "start_date": e.get("start_date"),
                "end_date": e.get("end_date"),
                "duration_years": duration_float,
                "description": e.get("description", ""),
            })

    # Normalise education entries
    raw_edu = inner.get("education", [])
    normalised_edu = []
    for e in raw_edu:
        if isinstance(e, dict):
            normalised_edu.append({
                "degree": e.get("degree", ""),
                "institution": e.get("institution", ""),
                "graduation_year": e.get("graduation_year"),
                "field_of_study": e.get("field_of_study"),
            })

    # Normalise projects
    raw_proj = inner.get("projects", [])
    normalised_proj = []
    for p in raw_proj:
        if isinstance(p, dict):
            normalised_proj.append({
                "name": p.get("name", ""),
                "description": p.get("description", ""),
                "technologies": p.get("technologies", []),
            })

    # contact_info
    contact = inner.get("contact_info") or {}

    return {
        "file_name": resolved_file_name,
        "upload_timestamp": inner.get("upload_timestamp", "2024-01-01T00:00:00"),
        "contact_info": {
            "name": contact.get("name"),
            "email": contact.get("email"),
            "phone": contact.get("phone"),
            "location": contact.get("location"),
            "linkedin": contact.get("linkedin"),
            "github": contact.get("github"),
        },
        "summary": inner.get("summary"),
        "skills": normalised_skills,
        "soft_skills": inner.get("soft_skills", []),
        "experience": normalised_exp,
        "education": normalised_edu,
        "projects": normalised_proj,
        "certifications": inner.get("certifications", []),
        "achievements": inner.get("achievements", []),
        "languages": inner.get("languages", []),
        "publications": inner.get("publications", []),
        "volunteer": inner.get("volunteer", []),
        "total_experience_years": float(inner.get("total_experience_years", 0.0)),
        "skill_count": int(inner.get("skill_count", len(normalised_skills))),
        "education_level": inner.get("education_level", ""),
    }


def _get_raw_text(parsed_data: Dict[str, Any]) -> Optional[str]:
    """Extract full resume text from our stored parsed_data structure."""
    text = parsed_data.get("full_text") or parsed_data.get("text")
    if not text:
        inner = parsed_data.get("parsed_data", {})
        if isinstance(inner, dict):
            text = inner.get("full_text") or inner.get("text") or inner.get("text_preview")
    return text or None


class MLClient:
    def __init__(self):
        self._base_url = ML_BASE_URL.rstrip("/") if ML_BASE_URL else None
        self._client = None

    @property
    def base_url(self) -> str:
        if not self._base_url:
            raise RuntimeError("ML service URL not configured. Set ML_PARSING_SERVICE_URL env var.")
        return self._base_url

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=5.0)
            )
        return self._client

    # ──────────────────────────────────────────────
    # POST /parse   (multipart/form-data)
    # ──────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def parse_resume(self, file_url: str) -> Dict[str, Any]:
        """
        Download the resume file and POST it to /parse.
        Returns the full parsed resume dict from the ML service.
        """
        # Refresh signed URL if it's a Supabase storage URL
        signed_url = file_url
        parsed = urlparse(file_url)
        path = parsed.path or ""
        bucket = settings.STORAGE_BUCKET_NAME
        for marker in [
            f"/storage/v1/object/public/{bucket}/",
            f"/storage/v1/object/sign/{bucket}/",
        ]:
            if marker in path:
                object_key = path.split(marker, 1)[1].lstrip("/")
                try:
                    signed_url = storage_service.get_file_url(object_key)
                except Exception:
                    pass
                break

        # Download file bytes
        file_resp = await self.client.get(signed_url)
        file_resp.raise_for_status()
        file_bytes = file_resp.content
        filename = path.rsplit("/", 1)[-1] or "resume.pdf"
        content_type = file_resp.headers.get("content-type", "application/pdf")

        # POST multipart to /parse
        response = await self.client.post(
            f"{self.base_url}/parse",
            files={"file": (filename, file_bytes, content_type)},
            timeout=120.0,
        )
        response.raise_for_status()
        result = response.json()

        if not isinstance(result, dict):
            raise ValueError(f"/parse returned non-dict: {type(result)}")

        logger.info(f"✅ /parse success. Keys: {list(result.keys())}")
        return result

    # ──────────────────────────────────────────────
    # POST /score   (JSON — ScoreRequest schema)
    # ──────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def score_resume(
        self,
        parsed_data: Dict[str, Any],
        mode: str = "baseline",
        required_skills: Optional[List[str]] = None,
        fairness_mode: str = "balanced",
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        POST /score with ScoreRequest schema.

        ScoreRequest:
          required_skills: list[str]   (required)
          resume: ParsedResume         (required)
          raw_text: str | null
          mode: str = "baseline"
          fairness_mode: str = "balanced"
          custom_ignore_fields: list[str] | null
          weights: dict | null
        """
        resume_obj = _build_parsed_resume(parsed_data)
        raw_text = _get_raw_text(parsed_data)

        payload = {
            "required_skills": required_skills or [],
            "resume": resume_obj,
            "raw_text": raw_text,
            "mode": mode,
            "fairness_mode": fairness_mode,
            "weights": weights,
        }

        logger.info(
            f"📤 POST /score | mode={mode} | skills={len(required_skills or [])} | "
            f"text_len={len(raw_text or '')} | file_name={resume_obj.get('file_name')}"
        )
        logger.debug(f"Payload keys: {list(payload.keys())}")
        logger.debug(f"Resume keys: {list(resume_obj.keys())}")

        response = await self.client.post(
            f"{self.base_url}/score",
            json=payload,
            timeout=180.0,
        )
        response.raise_for_status()
        result = response.json()

        # ScoreResponse fields:
        # score, mode, matched_skills, missing_skills, additional_skills,
        # short_explanation, components, weights_used, fairness_applied,
        # ignored_fields, gemini_score_used
        logger.info(f"✅ /score success. Score={result.get('score')} mode={result.get('mode')}")

        return {
            "overall_score": result.get("score", 0.0),
            "components": result.get("components", {}),
            "explanation": result.get("short_explanation", ""),
            "fairness_applied": result.get("fairness_applied", False),
            "matched_skills": result.get("matched_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "additional_skills": result.get("additional_skills", []),
            "weights_used": result.get("weights_used", {}),
            "ignored_fields": result.get("ignored_fields", []),
            "gemini_score_used": result.get("gemini_score_used"),
            "mode": result.get("mode", mode),
        }

    # ──────────────────────────────────────────────
    # POST /candidate-report   (JSON — CandidateReportRequest)
    # ──────────────────────────────────────────────
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def candidate_report(
        self,
        parsed_data: Dict[str, Any],
        required_skills: List[str],
        job_role: Optional[str] = None,
        mode: str = "enhanced",
        fairness_mode: str = "balanced",
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        POST /candidate-report with CandidateReportRequest schema.

        CandidateReportRequest:
          required_skills: list[str]   (required)
          resume: ParsedResume         (required)
          raw_text: str | null
          mode: str = "enhanced"
          fairness_mode: str = "balanced"
          custom_ignore_fields: list[str] | null
          weights: dict | null

        CandidateReportResponse fields:
          candidate_name, overall_score, verdict, score_breakdown,
          matched_skills, missing_skills, additional_skills,
          experience_years, education_level, soft_skills,
          project_count, certification_count, achievement_count,
          language_count, detailed_explanation, recommendations, weights_used
        """
        resume_obj = _build_parsed_resume(parsed_data)
        raw_text = _get_raw_text(parsed_data)

        payload = {
            "required_skills": required_skills or [],
            "resume": resume_obj,
            "raw_text": raw_text,
            "mode": mode,
            "fairness_mode": fairness_mode,
            "weights": weights,
        }

        logger.info(
            f"📋 POST /candidate-report | role={job_role or 'N/A'} | "
            f"skills={len(required_skills or [])} | mode={mode} | "
            f"text_len={len(raw_text or '')} | file_name={resume_obj.get('file_name')}"
        )
        logger.debug(f"Payload keys: {list(payload.keys())}")
        logger.debug(f"Resume keys: {list(resume_obj.keys())}")
        logger.debug(f"Experience entries: {len(resume_obj.get('experience', []))}")

        response = await self.client.post(
            f"{self.base_url}/candidate-report",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(
            f"✅ /candidate-report success. "
            f"Score={result.get('overall_score')} verdict={result.get('verdict')}"
        )

        return {
            "overall_score": result.get("overall_score", 0.0),
            "verdict": result.get("verdict", ""),
            "score_breakdown": result.get("score_breakdown", {}),
            "matched_skills": result.get("matched_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "additional_skills": result.get("additional_skills", []),
            "experience_years": result.get("experience_years", 0.0),
            "education_level": result.get("education_level", ""),
            "soft_skills": result.get("soft_skills", []),
            "project_count": result.get("project_count", 0),
            "certification_count": result.get("certification_count", 0),
            "recommendations": result.get("recommendations", []),
            "explanation": result.get("detailed_explanation", ""),
            "skill_match_percentage": (
                round(
                    len(result.get("matched_skills", [])) /
                    max(1, len(required_skills)) * 100, 1
                )
                if required_skills else 0.0
            ),
            "experience_level": _years_to_level(result.get("experience_years", 0.0)),
            "weights_used": result.get("weights_used", {}),
        }

    # ──────────────────────────────────────────────
    # POST /bias/detect   (JSON — BiasRequest)
    # ──────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_bias(
        self,
        candidates_data: List[Dict[str, str]],
        scores: List[float],
    ) -> Dict[str, Any]:
        """
        POST /bias/detect

        BiasRequest:
          scores: list[float]               (required)
          candidates_data: list[dict[str,str]]  (required)
        """
        payload = {
            "scores": scores,
            "candidates_data": candidates_data,
        }
        response = await self.client.post(
            f"{self.base_url}/bias/detect",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        logger.info("✅ /bias/detect success")
        return response.json()

    # ──────────────────────────────────────────────
    # POST /gemini/feedback   (JSON — FeedbackRequest)
    # ──────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_feedback(
        self,
        score_data: Dict[str, Any],
        parsed_data: Dict[str, Any],
    ) -> str:
        """
        POST /gemini/feedback

        FeedbackRequest:
          candidate_name: str    (required)
          score: float           (required)
          verdict: str           (required)
          missing_skills: list[str]  (required)
          experience_years: float    (required)
        """
        inner = parsed_data.get("parsed_data", parsed_data)
        contact = inner.get("contact_info") or {}
        candidate_name = contact.get("name") or "Candidate"

        payload = {
            "candidate_name": candidate_name,
            "score": float(score_data.get("overall_score", score_data.get("score", 0.0))),
            "verdict": score_data.get("verdict", "under_review"),
            "missing_skills": score_data.get("missing_skills", []),
            "experience_years": float(inner.get("total_experience_years", 0.0)),
        }

        response = await self.client.post(
            f"{self.base_url}/gemini/feedback",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        result = response.json()
        logger.info("✅ /gemini/feedback success")
        return result.get("feedback", result.get("text", ""))

    # ──────────────────────────────────────────────
    # POST /gemini/interview-questions
    # ──────────────────────────────────────────────
    async def generate_interview_questions(
        self,
        required_skills: List[str],
        missing_skills: List[str],
        resume_text: str,
    ) -> Dict[str, Any]:
        """
        POST /gemini/interview-questions

        InterviewQuestionsRequest:
          required_skills: list[str]
          missing_skills: list[str]
          resume_text: str
        """
        payload = {
            "required_skills": required_skills,
            "missing_skills": missing_skills,
            "resume_text": resume_text,
        }
        response = await self.client.post(
            f"{self.base_url}/gemini/interview-questions",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        logger.info("✅ /gemini/interview-questions success")
        return response.json()

    # ──────────────────────────────────────────────
    # POST /gemini/extract-skills
    # ──────────────────────────────────────────────
    async def extract_skills_from_jd(self, job_description: str) -> Dict[str, Any]:
        """
        POST /gemini/extract-skills

        JobDescriptionRequest:
          job_description: str
        """
        response = await self.client.post(
            f"{self.base_url}/gemini/extract-skills",
            json={"job_description": job_description},
            timeout=60.0,
        )
        response.raise_for_status()
        logger.info("✅ /gemini/extract-skills success")
        return response.json()

    # ──────────────────────────────────────────────
    # POST /gemini/summarise
    # ──────────────────────────────────────────────
    async def summarise_resume(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST /gemini/summarise — takes a ParsedResume object."""
        resume_obj = _build_parsed_resume(parsed_data)
        response = await self.client.post(
            f"{self.base_url}/gemini/summarise",
            json=resume_obj,
            timeout=60.0,
        )
        response.raise_for_status()
        logger.info("✅ /gemini/summarise success")
        return response.json()

    # ──────────────────────────────────────────────
    # POST /gemini/rank-candidates
    # ──────────────────────────────────────────────
    async def rank_candidates(
        self,
        candidates: List[Dict],
        job_description: str,
    ) -> Dict[str, Any]:
        """
        POST /gemini/rank-candidates

        RankCandidatesRequest:
          candidates: list[object]
          job_description: str
        """
        response = await self.client.post(
            f"{self.base_url}/gemini/rank-candidates",
            json={"candidates": candidates, "job_description": job_description},
            timeout=90.0,
        )
        response.raise_for_status()
        logger.info("✅ /gemini/rank-candidates success")
        return response.json()

    # ──────────────────────────────────────────────
    # POST /gemini/cultural-fit
    # ──────────────────────────────────────────────
    async def cultural_fit(
        self,
        resume_text: str,
        company_values: List[str],
    ) -> Dict[str, Any]:
        """
        POST /gemini/cultural-fit

        CulturalFitRequest:
          resume_text: str
          company_values: list[str]
        """
        response = await self.client.post(
            f"{self.base_url}/gemini/cultural-fit",
            json={"resume_text": resume_text, "company_values": company_values},
            timeout=60.0,
        )
        response.raise_for_status()
        logger.info("✅ /gemini/cultural-fit success")
        return response.json()

    # ──────────────────────────────────────────────
    # GET /skills
    # ──────────────────────────────────────────────
    async def get_skills(self) -> Dict[str, Any]:
        """GET /skills — returns the ML service's known skill list."""
        response = await self.client.get(f"{self.base_url}/skills", timeout=30.0)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client gracefully."""
        if self._client:
            await self._client.aclose()


def _years_to_level(years: float) -> str:
    if years < 2:
        return "Entry Level"
    elif years < 5:
        return "Mid Level"
    else:
        return "Senior Level"


# Singleton instance - lazy initialization at module level
_ml_client_instance = None

def get_ml_client() -> MLClient:
    """Get or create MLClient instance (lazy initialization)"""
    global _ml_client_instance
    if _ml_client_instance is None:
        _ml_client_instance = MLClient()
    return _ml_client_instance

# Backward compatibility - lazy wrapper
class _LazyMLClient:
    """Lazy wrapper that defers MLClient creation until first use"""
    def __getattr__(self, name: str):
        client = get_ml_client()
        return getattr(client, name)

ml_client = _LazyMLClient()