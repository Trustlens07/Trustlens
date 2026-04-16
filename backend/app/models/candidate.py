from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum
import uuid

class CandidateStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Candidate(BaseModel):
    __tablename__ = "candidates"
    __table_args__ = (UniqueConstraint("application_id", name="uq_application_id"),)
    
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(Enum(CandidateStatus), default=CandidateStatus.PENDING, nullable=False)
    parsed_data = Column(JSON, nullable=True)
    required_skills = Column(JSON, nullable=True)  # User-provided skills to match against
    job_role = Column(String(255), nullable=True)  # Job role for candidate report
    application_id = Column(String(50), unique=True, nullable=True)  # Unique app ID like APP-12345
    error_message = Column(String(500), nullable=True)
    screening_session_id = Column(String(255), ForeignKey("screening_sessions.id"), nullable=True)
    
    # Relationships
    scores = relationship("Score", back_populates="candidate", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="candidate", cascade="all, delete-orphan")
    screening_session = relationship("ScreeningSession", back_populates="candidates")
    decisions = relationship("Decision", back_populates="candidate", cascade="all, delete-orphan")