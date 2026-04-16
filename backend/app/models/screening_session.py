from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum
from datetime import datetime


class SessionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScreeningSession(BaseModel):
    __tablename__ = "screening_sessions"
    
    # Session metadata
    job_role = Column(String(255), nullable=False)
    job_description = Column(String(5000), nullable=True)
    fairness_mode = Column(String(50), default="balanced", nullable=False)  # balanced, strict, etc.
    
    # Results tracking
    total_candidates = Column(Integer, default=0, nullable=False)
    shortlisted_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    
    # Status
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING, nullable=False)
    error_message = Column(String(500), nullable=True)
    
    # Fairness metrics
    fairness_score = Column(Float, nullable=True)
    bias_metrics = Column(JSON, nullable=True)  # {gender: 0.95, age: 0.98, ...}
    
    # Relationships
    candidates = relationship("Candidate", back_populates="screening_session", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="session", cascade="all, delete-orphan")
