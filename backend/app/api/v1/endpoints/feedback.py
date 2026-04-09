from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.feedback import Feedback
from app.models.score import Score

router = APIRouter()

@router.get("/candidate/{candidate_id}")
async def get_feedback(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get feedback for a candidate"""
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
            "success": True,
            "data": None,
            "message": "No feedback available for this candidate"
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