from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey
from app.models.base import BaseModel
from sqlalchemy.dialects.postgresql import JSONB

class BiasMetric(BaseModel):
    __tablename__ = "bias_metrics"

    metric_name = Column(String(100), nullable=False)  # e.g., "demographic_parity", "equal_opportunity"
    group_type = Column(String(50), nullable=False)    # e.g., "gender", "ethnicity"
    group_name = Column(String(100), nullable=False)   # e.g., "female", "male"
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=True)
    is_biased = Column(String(10), nullable=False)     # "yes", "no", "warning"
    details = Column(JSON, nullable=True)              # Additional context
    calculated_at = Column(DateTime(timezone=True), nullable=False)

    # Link to candidate for enhanced bias analysis
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True)

    # Enhanced bias metrics (Gemini AI)
    is_enhanced = Column(String(10), default="no", nullable=False)  # "yes", "no"
    enhanced_bias_metrics = Column(JSONB, nullable=True)
    bias_enhanced_at = Column(DateTime(timezone=True), nullable=True)
    original_metric_id = Column(String(36), nullable=True)  # Reference to original metric if enhanced