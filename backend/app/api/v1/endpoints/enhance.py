"""Enhancement endpoint for ML service score enhancement."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.score import Score
from app.models.bias_metric import BiasMetric
from app.services.ml_client import ml_client
from app.api.v1.endpoints.auth import get_current_user   # <-- new import

router = APIRouter()
logger = logging.getLogger(__name__)


class EnhanceResponse(BaseModel):
    enhanced_score: float
    explanation: str
    bias_metrics: Optional[Dict[str, Any]] = None
    original_score: float


@router.post("/{candidate_id}/enhance", response_model=Dict[str, Any])
async def enhance_candidate_score(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)   # <-- new dependency
):
    # ... rest of your function (unchanged) ...
    """
    Enhance a candidate's score using ML service.

    This endpoint:
    1. Fetches the candidate's original score and resume data
    2. Calls ML service /enhance endpoint to get enhanced score
    3. Re-runs bias analysis on enhanced scores
    4. Stores enhanced results in database
    5. Returns enhanced score, explanation, and bias metrics

    Args:
        candidate_id: The candidate ID to enhance

    Returns:
        Enhanced score data with explanation and bias metrics

    Raises:
        404: If candidate or original score not found
        500: If ML service fails or returns invalid response
    """
    logger.info(f"Enhancement request for candidate: {candidate_id}")

    # Fetch candidate
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        logger.warning(f"Candidate not found: {candidate_id}")
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Fetch latest original score
    original_score = db.query(Score).filter(
        Score.candidate_id == candidate_id
    ).order_by(Score.created_at.desc()).first()

    if not original_score:
        logger.warning(f"No original score found for candidate: {candidate_id}")
        raise HTTPException(status_code=404, detail="No original score found for candidate")

    # Get resume text from parsed data
    resume_text = ""
    if candidate.parsed_data:
        if isinstance(candidate.parsed_data, dict):
            # Try to extract text from various fields
            resume_text = candidate.parsed_data.get("text", "")
            if not resume_text:
                # Concatenate relevant fields
                parts = []
                if "skills" in candidate.parsed_data:
                    parts.append(f"Skills: {candidate.parsed_data['skills']}")
                if "experience" in candidate.parsed_data:
                    parts.append(f"Experience: {candidate.parsed_data['experience']}")
                if "education" in candidate.parsed_data:
                    parts.append(f"Education: {candidate.parsed_data['education']}")
                resume_text = "\n".join(parts)

    # Get original bias metrics (if any)
    original_bias_metrics = None
    bias_metrics_rows = db.query(BiasMetric).filter(
        BiasMetric.candidate_id == candidate_id,
        BiasMetric.is_enhanced == "no"
    ).order_by(BiasMetric.calculated_at.desc()).all()

    if bias_metrics_rows:
        original_bias_metrics = {
            "metrics": [
                {
                    "metric_name": bm.metric_name,
                    "group_type": bm.group_type,
                    "group_name": bm.group_name,
                    "metric_value": bm.metric_value,
                    "is_biased": bm.is_biased
                }
                for bm in bias_metrics_rows[:5]  # Limit to first 5 metrics
            ]
        }

    try:
        # Call ML scoring service with mode="enhanced" for enhancement
        logger.info(f"Calling ML scoring service with mode=enhanced for candidate: {candidate_id}")

        # Use candidate's parsed_data for scoring with enhanced mode
        parsed_data_for_enhance = candidate.parsed_data if candidate.parsed_data else {}
        
        enhance_result = await ml_client.score_resume(
            parsed_data=parsed_data_for_enhance,
            mode="enhanced"
        )
        
        logger.info(f"Enhance result: score={enhance_result.get('overall_score')}, fairness={enhance_result.get('fairness_applied')}")

        # Store enhanced results in the score record
        enhanced_score_value = float(enhance_result.get("overall_score", original_score.overall_score))
        enhanced_breakdown = enhance_result.get("breakdown", original_score.breakdown)

        original_score.enhanced_score = enhanced_score_value
        original_score.enhanced_breakdown = enhanced_breakdown
        original_score.enhanced_at = datetime.now(timezone.utc)
        original_score.enhancement_explanation = enhance_result.get("explanation", "")
        original_score.bias_correction_applied = "Gemini AI" if enhance_result.get("fairness_applied") else "None"

        # Re-run bias analysis on enhanced scores
        enhanced_bias_metrics = None
        try:
            # Prepare candidate data for bias analysis with enhanced score
            candidates_data = []
            if candidate.parsed_data and isinstance(candidate.parsed_data, dict):
                # Extract protected attributes if available
                protected_attrs = candidate.parsed_data.get("protected_attributes", {})
                attributes = candidate.parsed_data.get("attributes", {})

                candidates_data.append({
                    "id": candidate_id,
                    "score": enhanced_score_value,
                    "protected_attributes": protected_attrs,
                    "attributes": attributes
                })

            if candidates_data:
                bias_result = await ml_client.analyze_bias(
                    candidates_data=candidates_data,
                    scores=[enhanced_score_value]
                )

                # Store enhanced bias metrics
                calculated_at = datetime.now(timezone.utc)

                # Store summary metrics
                if bias_result and isinstance(bias_result, dict):
                    enhanced_bias_metrics = bias_result

                    # Create BiasMetric records for enhanced analysis
                    for metric in bias_result.get("groups", []):
                        db.add(BiasMetric(
                            metric_name="enhanced_bias_analysis",
                            group_type=metric.get("group_type", "unknown"),
                            group_name=metric.get("group_name", "unknown"),
                            metric_value=metric.get("selection_rate", 0.0),
                            threshold=None,
                            is_biased="yes" if bias_result.get("summary", {}).get("is_biased", False) else "no",
                            details=metric,
                            calculated_at=calculated_at,
                            candidate_id=candidate_id,
                            is_enhanced="yes",
                            enhanced_bias_metrics=bias_result,
                            bias_enhanced_at=calculated_at
                        ))

        except Exception as e:
            logger.error(f"Enhanced bias analysis failed: {str(e)}")
            # Continue without enhanced bias metrics - don't fail the whole request
            enhanced_bias_metrics = {"error": "Bias analysis failed", "details": str(e)}

        # Commit all changes
        db.commit()

        logger.info(f"Enhancement successful for candidate: {candidate_id}. "
                    f"Score: {original_score.overall_score} -> {enhanced_score_value}")

        return {
            "success": True,
            "data": {
                "enhanced_score": enhanced_score_value,
                "enhanced_breakdown": enhanced_breakdown,
                "explanation": enhance_result.get("explanation", ""),
                "bias_correction_applied": "Gemini fairness applied" if enhance_result.get("fairness_applied") else "None",
                "bias_metrics": enhanced_bias_metrics,
                "original_score": original_score.overall_score,
                "enhanced_at": original_score.enhanced_at.isoformat() if original_score.enhanced_at else None,
                "mode": "enhanced"
            }
        }

    except Exception as e:
        logger.error(f"Enhancement failed for candidate {candidate_id}: {str(e)}")
        # Do NOT commit - original data remains unchanged
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement failed: {str(e)}"
        )
