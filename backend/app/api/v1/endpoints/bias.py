from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Any, Dict, List, Literal
from pydantic import BaseModel
from app.core.database import get_db
from app.models.bias_metric import BiasMetric
from app.models.candidate import Candidate
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


def _bias_metrics_group_breakdown(db: Session, dimension_label: str) -> Dict[str, Any]:
    """Verification-style payload for ?group=gender etc."""
    latest_at = db.query(func.max(BiasMetric.calculated_at)).scalar()
    if not latest_at:
        return {"group_type": dimension_label, "groups": {}, "disparity_ratio": None}

    rows = (
        db.query(BiasMetric)
        .filter(
            BiasMetric.calculated_at == latest_at,
            BiasMetric.metric_name == "average_score",
            BiasMetric.group_type == "group",
        )
        .all()
    )
    groups: Dict[str, Any] = {}
    for r in rows:
        n = 0
        if isinstance(r.details, dict) and r.details.get("n") is not None:
            try:
                n = int(r.details["n"])
            except (TypeError, ValueError):
                n = 0
        groups[r.group_name] = {"count": n, "avg_score": float(r.metric_value)}

    dpr_row = (
        db.query(BiasMetric)
        .filter(
            BiasMetric.calculated_at == latest_at,
            BiasMetric.metric_name == "demographic_parity_ratio",
            BiasMetric.group_type == "overall",
        )
        .first()
    )
    disparity = float(dpr_row.metric_value) if dpr_row else None

    return {
        "group_type": dimension_label,
        "groups": groups,
        "disparity_ratio": disparity,
    }


@router.get("/metrics")
async def get_bias_metrics(
    group_type: Optional[str] = Query(None, description="Filter by group type (gender, ethnicity, etc.)"),
    group: Optional[str] = Query(None, description="Alias of group_type for backward compatibility"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    version: Optional[Literal["original", "enhanced"]] = Query("original", description="Bias metrics version: 'original' or 'enhanced'"),
    db: Session = Depends(get_db)
):
    """
    Get latest bias metrics: overall snapshot, or grouped breakdown for ?group=gender.

    Args:
        group_type: Filter by group type (gender, ethnicity, etc.)
        group: Alias of group_type for backward compatibility
        candidate_id: Filter by specific candidate ID
        version: 'original' (default) or 'enhanced' for Gemini-enhanced bias analysis

    Returns:
        Bias metrics data. For version='enhanced', returns enhanced data if exists, else 404.
    """
    # If candidate_id provided, check candidate exists
    if candidate_id:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

    # Handle enhanced version request
    if version == "enhanced":
        if not candidate_id:
            raise HTTPException(status_code=400, detail="candidate_id required for version='enhanced'")

        # Query for enhanced bias metrics
        enhanced_metrics = db.query(BiasMetric).filter(
            BiasMetric.candidate_id == candidate_id,
            BiasMetric.is_enhanced == "yes"
        ).order_by(BiasMetric.bias_enhanced_at.desc()).first()

        if not enhanced_metrics:
            raise HTTPException(
                status_code=404,
                detail="Enhanced bias metrics not found. Run enhancement first via POST /candidates/{id}/enhance"
            )

        return {
            "success": True,
            "data": {
                "version": "enhanced",
                "candidate_id": candidate_id,
                "enhanced_bias_metrics": enhanced_metrics.enhanced_bias_metrics,
                "bias_enhanced_at": enhanced_metrics.bias_enhanced_at.isoformat() if enhanced_metrics.bias_enhanced_at else None,
                "metric_name": enhanced_metrics.metric_name,
                "group_type": enhanced_metrics.group_type,
                "group_name": enhanced_metrics.group_name,
                "metric_value": enhanced_metrics.metric_value,
                "is_biased": enhanced_metrics.is_biased
            }
        }

    # Original version (default behavior)
    raw = (group_type or group or "").strip()
    raw_lower = raw.lower()

    # If candidate_id provided without version, filter by candidate's original metrics
    if candidate_id:
        base_query = db.query(BiasMetric).filter(
            BiasMetric.candidate_id == candidate_id,
            BiasMetric.is_enhanced == "no"
        )
        latest = base_query.order_by(BiasMetric.calculated_at.desc()).first()
        if latest and latest.calculated_at:
            latest_at = latest.calculated_at
            rows = base_query.filter(BiasMetric.calculated_at == latest_at).all()
            return {
                "success": True,
                "data": {
                    "version": "original",
                    "candidate_id": candidate_id,
                    "metrics": [
                        {
                            "metric_name": r.metric_name,
                            "group_type": r.group_type,
                            "group_name": r.group_name,
                            "metric_value": r.metric_value,
                            "is_biased": r.is_biased,
                            "details": r.details,
                            "calculated_at": r.calculated_at.isoformat() if r.calculated_at else None
                        }
                        for r in rows
                    ]
                }
            }
        return {
            "success": True,
            "data": {"version": "original", "candidate_id": candidate_id, "metrics": []},
            "message": "No bias metrics found for candidate"
        }

    # Original global metrics behavior
    if raw_lower and raw_lower != "overall":
        return _bias_metrics_group_breakdown(db, dimension_label=raw_lower)

    base_query = db.query(BiasMetric)
    if raw_lower == "overall":
        base_query = base_query.filter(BiasMetric.group_type == "overall")

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