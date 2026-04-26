from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, unquote
from pydantic import BaseModel, EmailStr
from app.core.config import settings
from app.core.database import get_db
from app.services.storage_service import storage_service
from app.utils.file_validator import FileValidator
from app.models.candidate import Candidate, CandidateStatus
from app.orchestrators.upload_orchestrator import UploadOrchestrator
from app.models.score import Score
from app.models.feedback import Feedback
import logging
import re
from datetime import timezone, datetime

router = APIRouter()
logger = logging.getLogger(__name__)


def _iso_z(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _status_str(candidate: Candidate) -> str:
    s = candidate.status
    if isinstance(s, CandidateStatus):
        return s.value
    return str(s).lower()


def _extract_skills_from_parsed(parsed: dict) -> List[str]:
    """
    Job-role agnostic skill extraction from parsed_data.
    Handles both plain string lists and object lists like {"name": "python", ...}.
    Also checks nested parsed_data structures.
    """
    candidate_skills = []

    def extract_from_val(val):
        skills = []
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    name = item.get("name", "")
                    if name:
                        skills.extend([s.strip() for s in name.split(",") if s.strip()])
                elif isinstance(item, str) and item.strip():
                    skills.extend([s.strip() for s in item.split(",") if s.strip()])
        elif isinstance(val, str) and val.strip():
            skills.extend([s.strip() for s in val.split(",") if s.strip()])
        return skills

    if not isinstance(parsed, dict):
        return candidate_skills

    # Check top-level skill fields
    for field in ["skills", "technical_skills", "technologies", "tech_stack", "competencies", "expertise"]:
        val = parsed.get(field)
        if val:
            candidate_skills.extend(extract_from_val(val))

    # Check nested parsed_data structure
    if not candidate_skills:
        inner = parsed.get("parsed_data", {})
        if isinstance(inner, dict):
            for field in ["skills", "technical_skills", "technologies", "tech_stack", "competencies", "expertise"]:
                val = inner.get(field)
                if val:
                    candidate_skills.extend(extract_from_val(val))
                    if candidate_skills:
                        break

    return list(dict.fromkeys(candidate_skills))


def _extract_skills_from_text(text: str, required_skills: List[str]) -> List[str]:
    """Job-role agnostic fallback: extract skills from raw resume text."""
    if not text:
        return []

    if required_skills:
        text_lower = text.lower()
        return [skill for skill in required_skills if skill.lower() in text_lower]

    matches = re.findall(r'\b[A-Z][a-zA-Z0-9+#./]*(?:\s[A-Z][a-zA-Z0-9+#./]*){0,2}\b', text)
    stopwords = {
        "With", "The", "This", "In", "At", "For", "And", "Or", "To", "Of", "By",
        "On", "From", "Is", "Are", "Was", "Has", "Have", "Been", "When", "Where",
        "Senior", "Junior", "Lead", "Principal", "Staff", "Head", "Chief",
        "Manager", "Engineer", "Developer", "Designer", "Analyst", "Specialist",
        "Bachelor", "Master", "Doctor", "University", "College", "Institute",
        "Present", "Remote", "Onsite", "Hybrid", "Full", "Part", "Time",
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    }
    return [m for m in dict.fromkeys(matches) if m not in stopwords][:20]


def _get_full_text(parsed: dict) -> str:
    """Extract full resume text from parsed_data structure."""
    if not isinstance(parsed, dict):
        return ""
    text = parsed.get("full_text", "") or parsed.get("text", "")
    if not text:
        inner = parsed.get("parsed_data", {})
        if isinstance(inner, dict):
            text = inner.get("full_text", "") or inner.get("text", "")
    return text or ""


def _get_experience_years(parsed: dict):
    """
    Extract total years of experience from parsed_data.
    Checks top-level first (set by upload_orchestrator after fixing),
    then nested, then various field name aliases.
    """
    if not isinstance(parsed, dict):
        return None

    # Check top-level first — upload_orchestrator sets this correctly
    for field in ["total_experience_years", "years_of_experience", "experience_years"]:
        val = parsed.get(field)
        if val is not None:
            try:
                fval = float(val)
                if fval > 0:
                    return fval
            except (ValueError, TypeError):
                continue

    # Check nested parsed_data (older format)
    inner = parsed.get("parsed_data", {})
    if isinstance(inner, dict):
        for field in ["total_experience_years", "years_of_experience", "experience_years"]:
            val = inner.get(field)
            if val is not None:
                try:
                    fval = float(val)
                    if fval > 0:
                        return fval
                except (ValueError, TypeError):
                    continue

    return None


def _generate_basic_report(candidate: Candidate, required_skills: list) -> Dict[str, Any]:
    """
    Generate a basic report when ML service is not available.
    Job-role agnostic — works for any domain.
    
    Note: overall_score here is SKILL MATCH PERCENTAGE, not the pretrained score.
    The pretrained score (from /score endpoint) is stored separately in Score table
    and shown via /status endpoint.
    """
    parsed = candidate.parsed_data or {}
    status = candidate.status.value if isinstance(candidate.status, CandidateStatus) else str(candidate.status)

    # Step 1: Extract skills from structured parsed_data
    candidate_skills = _extract_skills_from_parsed(parsed)

    # Step 2: Fallback to text extraction if no structured skills
    if not candidate_skills:
        full_text = _get_full_text(parsed)
        candidate_skills = _extract_skills_from_text(full_text, required_skills)
        if candidate_skills:
            logger.info(f"Skills extracted from text for candidate {candidate.id}: {candidate_skills}")
        else:
            logger.warning(f"No skills could be extracted for candidate {candidate.id}")

    # Step 3: Match against required skills
    matched = []
    missing = []
    if required_skills and candidate_skills:
        cand_lower = [s.lower() for s in candidate_skills]
        matched = [s for s in required_skills if s.lower() in cand_lower]
        missing = [s for s in required_skills if s.lower() not in cand_lower]
    elif required_skills:
        # Last resort — scan full text
        full_text = _get_full_text(parsed)
        if full_text:
            text_lower = full_text.lower()
            matched = [s for s in required_skills if s.lower() in text_lower]
            missing = [s for s in required_skills if s.lower() not in text_lower]
        else:
            missing = required_skills

    # Step 4: Skill match percentage
    match_pct = (len(matched) / len(required_skills) * 100) if required_skills else 0.0

    # Step 5: Experience level
    exp_level = "Unknown"
    years = _get_experience_years(parsed)
    if years:
        try:
            years = float(years)
            if years < 2:
                exp_level = "Entry Level"
            elif years < 5:
                exp_level = "Mid Level"
            else:
                exp_level = "Senior Level"
        except (ValueError, TypeError):
            years = None

    # Step 6: Recommendations
    recommendations = []
    if status == "pending":
        recommendations.append("Resume is still being processed. Please check back in a moment.")
    elif status == "processing":
        recommendations.append("Resume is currently being analyzed by ML services.")
    elif status == "failed":
        recommendations.append("Resume processing failed. Please re-upload the file.")
    elif required_skills:
        recommendations.append(f"Candidate matches {len(matched)} of {len(required_skills)} required skills.")
        if missing:
            recommendations.append(f"Missing skills: {', '.join(missing[:5])}.")
        if matched:
            recommendations.append(f"Matched skills: {', '.join(matched[:5])}.")
    else:
        recommendations.append("No required skills specified. Add skills during upload for matching analysis.")

    # Step 7: Next steps
    next_steps = []
    if not required_skills:
        next_steps.append("Add required_skills during upload or via PUT /candidates/{id}/skills.")
    if not settings.ML_ENHANCE_SERVICE_URL:
        next_steps.append("Configure ML_ENHANCE_SERVICE_URL for AI-generated detailed reports.")
    if not next_steps:
        next_steps.append("Review matched and missing skills above for hiring decision.")

    return {
        "overall_score": round(match_pct, 1),
        "matched_skills": matched,
        "missing_skills": missing,
        "candidate_skills_found": candidate_skills[:20],
        "recommendations": recommendations,
        "explanation": (
            f"Basic report for {candidate.name or 'candidate'}: "
            f"{len(candidate_skills)} skills found, "
            f"{len(matched)}/{len(required_skills)} required skills matched. "
            f"Experience: {exp_level}"
            f"{f' ({years:.0f} years)' if isinstance(years, float) else ''}."
        ),
        "skill_match_percentage": round(match_pct, 1),
        "experience_level": exp_level,
        "years_of_experience": years,
        "processing_status": status,
        "next_steps": next_steps,
    }


def _skill_match_contract(raw: Dict[str, float]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = int(round(float(v)))
        except (TypeError, ValueError):
            continue
    return out


def _to_list(val) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v).strip() for v in val if str(v).strip()]
    if isinstance(val, str):
        parts = [p.strip() for p in val.split(",")]
        return [p for p in parts if p]
    return [str(val).strip()] if str(val).strip() else []


def _derive_skill_match(score_row: Optional[Score]) -> Dict[str, float]:
    if not score_row:
        return {}

    breakdown: Dict[str, Any] = (
        score_row.breakdown if isinstance(score_row.breakdown, dict) else {}
    )

    existing = breakdown.get("skill_match")
    if isinstance(existing, dict):
        normalized = {}
        for k, v in existing.items():
            try:
                normalized[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
        if normalized:
            return normalized

    matched = breakdown.get("matched_skills")
    missing = breakdown.get("missing_skills")
    if isinstance(matched, list):
        derived: Dict[str, float] = {}
        for skill in matched:
            key = str(skill).strip().lower()
            if key:
                derived[key] = 100.0
        if isinstance(missing, list):
            for skill in missing:
                key = str(skill).strip().lower()
                if key and key not in derived:
                    derived[key] = 0.0
        if derived:
            return derived

    mapping = {
        "skill": getattr(score_row, "skill_score", None),
        "experience": getattr(score_row, "experience_score", None),
        "education": getattr(score_row, "education_score", None),
    }
    return {
        k: float(v)
        for k, v in mapping.items()
        if isinstance(v, (int, float))
    }


def _derive_recommendations(feedback: Optional[Feedback], improvements: List[str]) -> str:
    text = (feedback.feedback_text or "").strip() if feedback else ""
    if text:
        return text
    if improvements:
        return "Consider improving: " + "; ".join(improvements[:3])
    return "No additional recommendations available yet."


class CandidateCreateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    file_id: Optional[str] = None
    storage_url: Optional[str] = None


def normalize_file_path(file_id: str) -> str:
    if file_id.startswith("http://") or file_id.startswith("https://"):
        parsed = urlparse(file_id)
        path = unquote(parsed.path)
        marker = f"/storage/v1/object/public/{settings.STORAGE_BUCKET_NAME}/"
        if marker in path:
            return path.split(marker, 1)[1]
        return path.split("/")[-1]
    if file_id.startswith(f"{settings.STORAGE_BUCKET_NAME}/"):
        return file_id[len(settings.STORAGE_BUCKET_NAME) + 1:]
    return file_id


def build_candidate_paths(file_reference: str) -> list[str]:
    bucket = settings.STORAGE_BUCKET_NAME
    normalized = normalize_file_path(file_reference)
    candidates = [normalized]

    if normalized.startswith(f"{bucket}/"):
        candidates.append(normalized[len(bucket) + 1:])
        candidates.append(f"{bucket}/{normalized}")
    else:
        candidates.append(f"{bucket}/{normalized}")
        candidates.append(f"{bucket}/{bucket}/{normalized}")

    if normalized.startswith(f"{bucket}/{bucket}/"):
        candidates.append(normalized[len(bucket) + 1:])
        candidates.append(normalized[len(bucket) * 2 + 2:])
        candidates.append(f"{bucket}/{normalized}")

    if "/" in normalized:
        parts = normalized.split("/")
        if parts[0] == bucket and parts[1] == bucket:
            candidates.append("/".join(parts[1:]))
            candidates.append("/".join(parts[2:]))

    seen = set()
    final = []
    for path in candidates:
        if path and path not in seen:
            seen.add(path)
            final.append(path)
    return final


@router.post("")
async def create_candidate(
    candidate_request: CandidateCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a candidate record from an existing uploaded file"""
    try:
        if not candidate_request.storage_url and not candidate_request.file_id:
            raise HTTPException(status_code=400, detail="Either file_id or storage_url must be provided")

        reference = candidate_request.storage_url or candidate_request.file_id
        candidate_file_path = None
        file_url = None
        tried_paths = build_candidate_paths(reference)

        for path in tried_paths:
            try:
                file_url = storage_service.get_file_url(path)
                candidate_file_path = path
                break
            except Exception:
                continue

        if file_url is None:
            raise HTTPException(status_code=404, detail=f"File not found in storage. Tried: {tried_paths}")

        file_name = candidate_file_path.split("/")[-1]
        file_type = FileValidator.get_content_type(file_name)

        candidate = Candidate(
            name=candidate_request.name,
            email=candidate_request.email,
            file_name=file_name,
            file_url=file_url,
            file_size=0,
            file_type=file_type,
            status=CandidateStatus.PENDING
        )

        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        return {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "file_id": candidate.file_name,
            "status": _status_str(candidate),
            "created_at": _iso_z(candidate.created_at),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Candidate creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Candidate creation failed: {str(e)}")


@router.get("")
async def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[CandidateStatus] = None,
    db: Session = Depends(get_db)
):
    """List all candidates with pagination"""
    query = db.query(Candidate)
    if status:
        query = query.filter(Candidate.status == status)

    candidates = query.offset(skip).limit(limit).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "status": _status_str(c),
            "created_at": _iso_z(c.created_at),
        }
        for c in candidates
    ]


@router.post("/{candidate_id}/process")
async def process_candidate(
    candidate_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger async ML pipeline for an existing candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if not candidate.file_url:
        raise HTTPException(status_code=400, detail="Candidate has no file_url")

    candidate.status = CandidateStatus.PROCESSING
    candidate.error_message = None
    db.commit()

    background_tasks.add_task(
        UploadOrchestrator.process_resume,
        candidate_id,
        candidate.file_url,
    )

    return {
        "candidate_id": candidate_id,
        "status": "processing_started",
        "message": "ML pipeline triggered",
    }


@router.get("/{candidate_id}/status")
async def get_candidate_status(
    candidate_id: str,
    db: Session = Depends(get_db),
):
    """Polling endpoint: status + latest overall score + processed timestamp."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    score_row = (
        db.query(Score)
        .filter(Score.candidate_id == candidate_id)
        .order_by(Score.version.desc(), Score.created_at.desc())
        .first()
    )

    status_val = candidate.status.value if isinstance(candidate.status, CandidateStatus) else str(candidate.status)

    processed_at = candidate.updated_at
    if processed_at is not None:
        if processed_at.tzinfo is None:
            processed_at = processed_at.replace(tzinfo=timezone.utc)
        processed_at = processed_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        processed_at = None

    payload = {
        "candidate_id": candidate_id,
        "status": status_val,
        "score": score_row.overall_score if score_row else None,
        "processed_at": processed_at,
    }
    if candidate.error_message:
        payload["error"] = candidate.error_message
    return payload


@router.get("/{candidate_id}/feedback")
async def get_candidate_feedback_alias(
    candidate_id: str,
    db: Session = Depends(get_db),
):
    """Alias for GET /api/v1/feedback/candidate/{candidate_id} with flattened contract."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    feedback = (
        db.query(Feedback)
        .filter(Feedback.candidate_id == candidate_id)
        .order_by(Feedback.created_at.desc())
        .first()
    )
    score_row = (
        db.query(Score)
        .filter(Score.candidate_id == candidate_id)
        .order_by(Score.version.desc(), Score.created_at.desc())
        .first()
    )
    if not feedback:
        return {
            "candidate_id": candidate_id,
            "score": score_row.overall_score if score_row else None,
            "strengths": [],
            "improvements": [],
            "skill_match": _skill_match_contract(_derive_skill_match(score_row)),
            "recommendations": "No feedback generated yet.",
        }
    strengths = _to_list(feedback.strengths)
    improvements = _to_list(feedback.improvements)

    return {
        "candidate_id": candidate_id,
        "score": score_row.overall_score if score_row else None,
        "strengths": strengths,
        "improvements": improvements,
        "skill_match": _skill_match_contract(_derive_skill_match(score_row)),
        "recommendations": _derive_recommendations(feedback, improvements),
    }


@router.get("/{candidate_id}/report")
async def get_candidate_report(
    candidate_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed candidate report.

    Tries ML /candidate-report first (Gemini enhanced).
    Falls back to basic skill-match report if ML unavailable.

    NOTE: report.overall_score = skill match percentage (0-100%)
          NOT the same as the pretrained score shown in /status.
          Pretrained score is stored in Score table, shown via /status.
    """
    from app.services.ml_client import ml_client

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if not candidate.parsed_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate data not yet processed. Please wait for processing to complete."
        )

    required_skills = candidate.required_skills or []
    job_role = candidate.job_role or "Not specified"

    report = None
    ml_service_error = None

    if settings.ML_ENHANCE_SERVICE_URL:
        try:
            report = await ml_client.candidate_report(
                parsed_data=candidate.parsed_data,
                required_skills=required_skills,
                job_role=job_role
            )
            # Validate response is useful
            if not report or report.get("overall_score", 0) == 0 and not report.get("matched_skills"):
                logger.warning(f"ML returned empty report for candidate {candidate_id}, using fallback")
                report = None
            else:
                logger.info(f"ML report generated for candidate {candidate_id}")
        except Exception as e:
            ml_service_error = str(e)
            logger.warning(f"ML service failed for {candidate_id}: {ml_service_error}")

    if report is None:
        report = _generate_basic_report(candidate, required_skills)
        if ml_service_error:
            report["ml_service_error"] = "ML service unavailable, showing basic report"

    return {
        "candidate_id": candidate_id,
        "application_id": candidate.application_id,
        "name": candidate.name,
        "email": candidate.email,
        "job_role": job_role,
        "report": report,
        "generated_at": _iso_z(datetime.now(timezone.utc)),
    }


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get candidate details by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "file_id": candidate.file_name,
        "status": _status_str(candidate),
        "created_at": _iso_z(candidate.created_at),
        "phone": candidate.phone,
        "file_url": candidate.file_url,
        "file_size": candidate.file_size,
        "file_type": candidate.file_type,
        "parsed_data": candidate.parsed_data,
        "required_skills": candidate.required_skills,
        "error_message": candidate.error_message,
        "updated_at": _iso_z(candidate.updated_at),
    }


class UpdateSkillsRequest(BaseModel):
    required_skills: List[str]


@router.put("/{candidate_id}/skills")
async def update_candidate_skills(
    candidate_id: str,
    request: UpdateSkillsRequest,
    db: Session = Depends(get_db)
):
    """Update required skills for a candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.required_skills = request.required_skills
    db.commit()
    db.refresh(candidate)

    return {
        "success": True,
        "candidate_id": candidate.id,
        "required_skills": candidate.required_skills,
        "message": f"Updated {len(request.required_skills)} skills",
    }


@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Delete candidate and all related data"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    db.delete(candidate)
    db.commit()

    return {
        "success": True,
        "message": f"Candidate {candidate_id} deleted successfully",
    }