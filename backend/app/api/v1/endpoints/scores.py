from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.score import Score

router = APIRouter()

@router.get("/candidate/{candidate_id}")
async def get_candidate_scores(
    candidate_id: str,
    version: Optional[Literal["original", "enhanced"]] = Query("original", description="Score version: 'original' or 'enhanced'"),
    db: Session = Depends(get_db)
):
    """
    Get scores for a candidate.

    Args:
        candidate_id: The candidate ID
        version: 'original' (default) or 'enhanced' for Gemini-enhanced scores

    Returns:
        Score data. For version='enhanced', returns enhanced data if exists, else 404.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    score = db.query(Score).filter(Score.candidate_id == candidate_id).order_by(Score.created_at.desc()).first()
    if not score:
        return {
            "success": True,
            "data": None,
            "message": "No scores available for this candidate"
        }

    # Return enhanced version if requested and available
    if version == "enhanced":
        if score.enhanced_score is None:
            raise HTTPException(
                status_code=404,
                detail="Enhanced score not found. Run enhancement first via POST /candidates/{id}/enhance"
            )

        return {
            "success": True,
            "data": {
                "id": score.id,
                "candidate_id": score.candidate_id,
                "overall_score": score.enhanced_score,
                "skill_score": score.enhanced_breakdown.get("skills") if score.enhanced_breakdown else None,
                "experience_score": score.enhanced_breakdown.get("experience") if score.enhanced_breakdown else None,
                "education_score": score.enhanced_breakdown.get("education") if score.enhanced_breakdown else None,
                "breakdown": score.enhanced_breakdown,
                "ranking_percentile": score.ranking_percentile,
                "version": "enhanced",
                "enhanced_at": score.enhanced_at.isoformat() if score.enhanced_at else None,
                "enhanced_by_model": score.enhanced_by_model,
                "explanation": score.enhancement_explanation,
                "bias_correction_applied": score.bias_correction_applied,
                "created_at": score.created_at.isoformat() if score.created_at else None
            }
        }

    # Return original version (default)
    return {
        "success": True,
        "data": {
            "id": score.id,
            "candidate_id": score.candidate_id,
            "overall_score": score.overall_score,
            "skill_score": score.skill_score,
            "experience_score": score.experience_score,
            "education_score": score.education_score,
            "breakdown": score.breakdown,
            "ranking_percentile": score.ranking_percentile,
            "version": "original",
            "created_at": score.created_at.isoformat() if score.created_at else None
        }
    }

@router.get("/candidate/{candidate_id}/history")
async def get_score_history(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get all score versions for a candidate"""
    scores = db.query(Score).filter(Score.candidate_id == candidate_id).order_by(Score.created_at.desc()).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "overall_score": s.overall_score,
                "version": s.version,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in scores
        ]
    }