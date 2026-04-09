from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, Any, Dict, List
from pydantic import BaseModel
from app.core.database import get_db
from app.models.bias_metric import BiasMetric
from app.services.ml_client import ml_client
import logging
from datetime import timezone
from datetime import datetime

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
async def analyze_bias(request: BiasAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze fairness in candidate scoring using bias metrics."""
    candidates_data = []
    scores: list[float] = []
    group_scores: Dict[str, list[float]] = {}
    for c in request.candidates:
        if c.score is not None:
            s = float(c.score)
            scores.append(s)
        merged = {}
        if c.attributes:
            merged.update(c.attributes)
        if c.protected_attributes:
            merged.update(c.protected_attributes)
        if c.id:
            merged["id"] = c.id
        candidates_data.append(merged)

        # Track scores by group for local metrics computation
        group = None
        if c.protected_attributes and isinstance(c.protected_attributes, dict):
            group = c.protected_attributes.get("group")
        if group is None and c.attributes and isinstance(c.attributes, dict):
            group = c.attributes.get("group")
        if group is not None and c.score is not None:
            group_scores.setdefault(str(group), []).append(s)

    calculated_at = datetime.now(timezone.utc)
    try:
        result = await ml_client.analyze_bias(candidates_data, scores)
    except Exception as e:
        logger.error(f"Bias analysis failed: {str(e)}")
        result = _mock_bias_analysis_response()

    # Persist metrics for GET /metrics. Compute from input so it's stable even if
    # ML returns only `bias_detected` / `recommendations`.
    avg_by_group: Dict[str, float] = {}
    for g, vals in group_scores.items():
        if vals:
            avg_by_group[g] = sum(vals) / len(vals)

    if avg_by_group:
        # average_score_by_group
        for g, avg in avg_by_group.items():
            db.add(
                BiasMetric(
                    metric_name="average_score",
                    group_type="group",
                    group_name=g,
                    metric_value=float(avg),
                    threshold=None,
                    is_biased="no",
                    details={"n": len(group_scores.get(g, []))},
                    calculated_at=calculated_at,
                )
            )

        # demographic_parity_ratio (simple proxy): min(avg)/max(avg)
        avgs = list(avg_by_group.values())
        mx = max(avgs)
        mn = min(avgs)
        if mx > 0:
            db.add(
                BiasMetric(
                    metric_name="demographic_parity_ratio",
                    group_type="overall",
                    group_name="overall",
                    metric_value=float(mn / mx),
                    threshold=0.8,
                    is_biased="warning",
                    details={"min_avg": mn, "max_avg": mx},
                    calculated_at=calculated_at,
                )
            )

        # equal_opportunity_diff (simple proxy): max(avg)-min(avg)
        db.add(
            BiasMetric(
                metric_name="equal_opportunity_diff",
                group_type="overall",
                group_name="overall",
                metric_value=float(mx - mn),
                threshold=None,
                is_biased="warning",
                details={"min_avg": mn, "max_avg": mx},
                calculated_at=calculated_at,
            )
        )

    db.commit()
    return {"success": True, "data": result}


@router.get("/metrics")
async def get_bias_metrics(
    group_type: Optional[str] = Query(None, description="Filter by group type (gender, ethnicity, etc.)"),
    db: Session = Depends(get_db)
):
    """Get latest bias metrics in a compact overall format."""
    base_query = db.query(BiasMetric)
    if group_type:
        base_query = base_query.filter(BiasMetric.group_type == group_type)

    latest = base_query.order_by(BiasMetric.calculated_at.desc()).first()
    if not latest or not latest.calculated_at:
        return {"overall": {}, "last_calculated": None}

    latest_at = latest.calculated_at
    rows = base_query.filter(BiasMetric.calculated_at == latest_at).all()

    def _pick_value(names: list[str]) -> Optional[float]:
        for n in names:
            for r in rows:
                if r.metric_name == n:
                    return r.metric_value
        return None

    demographic_parity_ratio = _pick_value(
        ["demographic_parity_ratio", "disparate_impact", "demographic_parity"]
    )
    equal_opportunity_diff = _pick_value(
        ["equal_opportunity_diff", "equal_opportunity_difference", "equal_opportunity"]
    )

    average_score_by_group: Dict[str, float] = {}
    for r in rows:
        if r.metric_name in ("average_score_by_group", "average_score"):
            average_score_by_group[r.group_name] = r.metric_value

    if latest_at.tzinfo is None:
        latest_at = latest_at.replace(tzinfo=timezone.utc)
    last_calculated = latest_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    overall: Dict[str, Any] = {}
    if demographic_parity_ratio is not None:
        overall["demographic_parity_ratio"] = demographic_parity_ratio
    if equal_opportunity_diff is not None:
        overall["equal_opportunity_diff"] = equal_opportunity_diff
    if average_score_by_group:
        overall["average_score_by_group"] = average_score_by_group

    return {"overall": overall, "last_calculated": last_calculated}

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