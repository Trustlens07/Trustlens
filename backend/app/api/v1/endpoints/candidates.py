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

    # Preferred shape from ML output.
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

    # Fallback 1: derive from explicit matched/missing skills.
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

    # Fallback 2: derive from score components.
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
    # Accept either a raw storage path, a bucket-relative path, or a Supabase storage URL.
    if file_id.startswith("http://") or file_id.startswith("https://"):
        parsed = urlparse(file_id)
        path = unquote(parsed.path)
        marker = f"/storage/v1/object/public/{settings.STORAGE_BUCKET_NAME}/"
        if marker in path:
            return path.split(marker, 1)[1]
        return path.split("/")[-1]

    if file_id.startswith(f"{settings.STORAGE_BUCKET_NAME}/"):
        return file_id[len(settings.STORAGE_BUCKET_NAME) + 1 :]

    return file_id


def build_candidate_paths(file_reference: str) -> list[str]:
    bucket = settings.STORAGE_BUCKET_NAME
    normalized = normalize_file_path(file_reference)
    candidates = [normalized]

    if normalized.startswith(f"{bucket}/"):
        candidates.append(normalized[len(bucket) + 1 :])
        candidates.append(f"{bucket}/{normalized}")
    else:
        candidates.append(f"{bucket}/{normalized}")
        candidates.append(f"{bucket}/{bucket}/{normalized}")

    if normalized.startswith(f"{bucket}/{bucket}/"):
        candidates.append(normalized[len(bucket) + 1 :])
        candidates.append(normalized[len(bucket) * 2 + 2 :])
        candidates.append(f"{bucket}/{normalized}")

    if "/" in normalized:
        parts = normalized.split("/")
        if parts[0] == bucket and parts[1] == bucket:
            candidates.append("/".join(parts[1:]))
            candidates.append("/".join(parts[2:]))

    # Preserve ordering and uniqueness
    seen = set()
    final = []
    for path in candidates:
        if path and path not in seen:
            seen.add(path)
            final.append(path)
    return final


@router.post("/")
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

@router.get("/")
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

    # Mark processing immediately so polling reflects the change.
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
    """Update required skills for a candidate
    
    Args:
        candidate_id: The candidate ID
        required_skills: List of skills to match against the resume
    
    Example:
        PUT /candidates/{id}/skills
        {
            "required_skills": ["Python", "JavaScript", "AWS"]
        }
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Update required skills
    candidate.required_skills = request.required_skills
    db.commit()
    db.refresh(candidate)
    
    return {
        "success": True,
        "candidate_id": candidate.id,
        "required_skills": candidate.required_skills,
        "message": f"Updated {len(request.required_skills)} skills"
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
    
    # Optionally delete file from storage here (implement if needed)
    db.delete(candidate)
    db.commit()
    
    return {
        "success": True,
        "message": f"Candidate {candidate_id} deleted successfully"
    }