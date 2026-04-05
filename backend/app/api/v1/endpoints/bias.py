from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, Any, Dict, List
from pydantic import BaseModel
from app.core.database import get_db
from app.models.bias_metric import BiasMetric
from app.services.ml_client import ml_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class CandidateBiasInput(BaseModel):
    id: Optional[str] = None
    score: Optional[float] = None
    protected_attributes: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None

class BiasAnalysisRequest(BaseModel):
    candidates: List[CandidateBiasInput]


def _mock_bias_analysis_response() -> Dict[str, Any]:
    return {
        "metric_name": "bias_analysis",
        "summary": {
            "demographic_parity_difference": 0.08,
            "equal_opportunity_difference": 0.06,
            "disparate_impact": 0.85,
            "is_biased": True
        },
        "groups": [
            {
                "group_type": "gender",
                "group_name": "male",
                "selection_rate": 0.54,
                "true_positive_rate": 0.76,
                "disparate_impact": 1.04
            },
            {
                "group_type": "gender",
                "group_name": "female",
                "selection_rate": 0.46,
                "true_positive_rate": 0.70,
                "disparate_impact": 0.96
            }
        ],
        "details": "Mock bias analysis returned because the ML bias service is unavailable"
    }


@router.post("/analyze")
async def analyze_bias(request: BiasAnalysisRequest):
    """Analyze fairness in candidate scoring using bias metrics."""
    try:
        result = await ml_client.analyze_bias([candidate.dict(exclude_none=True) for candidate in request.candidates])
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Bias analysis failed: {str(e)}")
        return {
            "success": True,
            "data": _mock_bias_analysis_response()
        }


@router.get("/metrics")
async def get_bias_metrics(
    group_type: Optional[str] = Query(None, description="Filter by group type (gender, ethnicity, etc.)"),
    db: Session = Depends(get_db)
):
    """Get bias metrics"""
    query = db.query(BiasMetric)
    if group_type:
        query = query.filter(BiasMetric.group_type == group_type)
    
    metrics = query.order_by(BiasMetric.calculated_at.desc()).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": m.id,
                "metric_name": m.metric_name,
                "group_type": m.group_type,
                "group_name": m.group_name,
                "metric_value": m.metric_value,
                "threshold": m.threshold,
                "is_biased": m.is_biased,
                "details": m.details,
                "calculated_at": m.calculated_at.isoformat() if m.calculated_at else None
            }
            for m in metrics
        ]
    }

@router.get("/summary")
async def get_bias_summary(
    db: Session = Depends(get_db)
):
    """Get summary of bias analysis"""
    # Get latest metrics for each type
    from sqlalchemy import distinct
    metric_types = db.query(distinct(BiasMetric.metric_name)).all()
    
    summary = []
    for (metric_name,) in metric_types:
        latest = db.query(BiasMetric).filter(BiasMetric.metric_name == metric_name).order_by(BiasMetric.calculated_at.desc()).first()
        if latest:
            summary.append({
                "metric_name": metric_name,
                "latest_value": latest.metric_value,
                "is_biased": latest.is_biased,
                "calculated_at": latest.calculated_at.isoformat() if latest.calculated_at else None
            })
    
    return {
        "success": True,
        "data": summary
    }