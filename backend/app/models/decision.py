from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum
from datetime import datetime, timezone


class DecisionStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"


class Decision(BaseModel):
    __tablename__ = "decisions"
    
    application_id = Column(String(255), nullable=False, unique=True, index=True)
    candidate_id = Column(String(255), ForeignKey("candidates.id"), nullable=False)
    session_id = Column(String(255), ForeignKey("screening_sessions.id"), nullable=False)
    
    decision = Column(Enum(DecisionStatus), default=DecisionStatus.PENDING, nullable=False)
    notes = Column(String(500), nullable=True)
    decided_by = Column(String(255), nullable=True)  # User who made the decision
    
    # Relationships
    candidate = relationship("Candidate", back_populates="decisions")
    session = relationship("ScreeningSession", back_populates="decisions")
