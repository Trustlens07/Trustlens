from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
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
from datetime import timezone

router = APIRouter()
logger = logging.getLogger(__name__)

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
            "success": True,
            "message": "Candidate record created successfully",
            "data": {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "file_name": candidate.file_name,
                "file_url": candidate.file_url,
                "status": candidate.status,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None
            }
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
    
    total = query.count()
    candidates = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "status": c.status,
                    "file_name": c.file_name,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in candidates
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }

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
            "skill_match": {},
            "recommendations": "",
        }

    def _to_list(val):
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            parts = [p.strip() for p in val.split(",")]
            return [p for p in parts if p]
        return [str(val)]

    breakdown = score_row.breakdown if score_row and isinstance(score_row.breakdown, dict) else {}
    skill_match = breakdown.get("skill_match") if isinstance(breakdown.get("skill_match"), dict) else {}

    return {
        "candidate_id": candidate_id,
        "score": score_row.overall_score if score_row else None,
        "strengths": _to_list(feedback.strengths),
        "improvements": _to_list(feedback.improvements),
        "skill_match": skill_match,
        "recommendations": feedback.feedback_text or "",
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
        "success": True,
        "data": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "file_name": candidate.file_name,
            "file_url": candidate.file_url,
            "file_size": candidate.file_size,
            "file_type": candidate.file_type,
            "status": candidate.status,
            "parsed_data": candidate.parsed_data,
            "error_message": candidate.error_message,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None
        }
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