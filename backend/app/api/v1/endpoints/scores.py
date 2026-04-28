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
    version: Optional[Literal["original", "enhanced"]] = Query("original"),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    score = db.query(Score).filter(Score.candidate_id == candidate_id).order_by(Score.created_at.desc()).first()
    if not score:
        return {"success": True, "data": None, "message": "No scores available for this candidate"}

    if version == "enhanced":
        if score.enhanced_score is None:
            raise HTTPException(status_code=404, detail="Enhanced score not found. Run enhancement first.")

        enhanced_breakdown = score.enhanced_breakdown or {}
        score_breakdown = enhanced_breakdown.get("score_breakdown", enhanced_breakdown)

        return {
            "success": True,
            "data": {
                "id": str(score.id),
                "candidate_id": str(score.candidate_id),
                "overall_score": float(score.enhanced_score or 0),
                "skill_score": float(score_breakdown.get("skills", 0) if isinstance(score_breakdown.get("skills"), (int, float)) else 0),
                "experience_score": float(score_breakdown.get("experience", 0)),
                "education_score": float(score_breakdown.get("education", 0)),
                "breakdown": {
                    "skills": _extract_skills(score_breakdown.get("skills", {})),
                    "experience": float(score_breakdown.get("experience", 0)),
                    "education": float(score_breakdown.get("education", 0)),
                    "projects": float(score_breakdown.get("projects", 0)),
                    "soft_skills": float(score_breakdown.get("soft_skills", 0)),
                },
                "ranking_percentile": score.ranking_percentile,
                "version": "enhanced",
                "explanation": score.enhancement_explanation or "",
                "bias_correction_applied": score.bias_correction_applied or "",
                "enhanced_at": score.enhanced_at.isoformat() if score.enhanced_at else None,
                "enhanced_by_model": score.enhanced_by_model,
                "created_at": score.created_at.isoformat() if score.created_at else None,
            }
        }

    # Original version
    breakdown = score.breakdown or {}

    # Calculate overall_score if it's 0 but sub-scores exist
    overall = float(score.overall_score or 0)
    exp = float(score.experience_score or 0)
    edu = float(score.education_score or 0)
    skl = float(score.skill_score or 0)
    proj = float(breakdown.get("projects", 0))

    if overall == 0 and (exp + edu + skl + proj) > 0:
        overall = round((skl * 0.35) + (exp * 0.30) + (edu * 0.20) + (proj * 0.15), 1)

    # soft_skills — always return a number
    raw_soft = breakdown.get("soft_skills", 0)
    soft_skills_score = float(raw_soft) if isinstance(raw_soft, (int, float)) else 0.0

    return {
        "success": True,
        "data": {
            "id": str(score.id),
            "candidate_id": str(score.candidate_id),
            "overall_score": overall,
            "skill_score": float(score.skill_score or 0),
            "experience_score": float(score.experience_score or 0),
            "education_score": float(score.education_score or 0),
            "breakdown": {
                "skills": _extract_skills(breakdown.get("skills", [])),
                "experience": float(breakdown.get("experience", score.experience_score or 0)),
                "education": float(breakdown.get("education", score.education_score or 0)),
                "projects": float(breakdown.get("projects", 0)),
                "soft_skills": soft_skills_score,
            },
            "ranking_percentile": score.ranking_percentile,
            "version": "original",
            "explanation": "",
            "created_at": score.created_at.isoformat() if score.created_at else None,
        }
    }


def _extract_skills(raw) -> dict:
    """Always returns {skill_name: score} dict regardless of input format."""
    if isinstance(raw, dict):
        return {k: float(v) for k, v in raw.items() if isinstance(v, (int, float))}
    if isinstance(raw, list):
        result = {}
        for item in raw:
            if isinstance(item, dict):
                name = item.get("name") or item.get("skill") or "unknown"
                score = item.get("score", 0)
                result[name] = float(score)
        return result
    return {}


@router.get("/candidate/{candidate_id}/history")
async def get_score_history(candidate_id: str, db: Session = Depends(get_db)):
    scores = db.query(Score).filter(Score.candidate_id == candidate_id).order_by(Score.created_at.desc()).all()
    return {
        "success": True,
        "data": [
            {
                "id": str(s.id),
                "overall_score": float(s.overall_score or 0),
                "version": s.version,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in scores
        ]
    }