from sqlalchemy import Column, String, Float, JSON, ForeignKey, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from sqlalchemy.dialects.postgresql import JSONB

class Score(BaseModel):
    __tablename__ = "scores"

    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)
    skill_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    breakdown = Column(JSON, nullable=False)  # Detailed breakdown of each category
    ranking_percentile = Column(Float, nullable=True)
    version = Column(Integer, default=1, nullable=False)  # For tracking re-scores

    # Enhanced fields (Gemini AI)
    enhanced_score = Column(Float, nullable=True)
    enhanced_breakdown = Column(JSONB, nullable=True)
    enhanced_at = Column(DateTime(timezone=True), nullable=True)
    enhanced_by_model = Column(String(100), default="gemini-1.5-pro")
    enhancement_explanation = Column(Text, nullable=True)
    bias_correction_applied = Column(Text, nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="scores")