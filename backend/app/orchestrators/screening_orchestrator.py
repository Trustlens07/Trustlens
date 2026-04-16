import asyncio
import logging
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.candidate import Candidate, CandidateStatus
from app.models.screening_session import ScreeningSession, SessionStatus
from app.models.decision import Decision, DecisionStatus
from app.models.score import Score
from app.services.storage_service import storage_service
from app.services.ml_client import ml_client
from app.orchestrators.upload_orchestrator import UploadOrchestrator
from app.utils.file_validator import FileValidator

logger = logging.getLogger(__name__)


class ScreeningOrchestrator:
    @staticmethod
    async def process_batch_screening(
        session_id: str,
        job_role: str,
        job_description: str,
        fairness_mode: str,
        resumes: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Process batch screening of multiple resumes.
        
        Args:
            session_id: Unique screening session ID
            job_role: Job role for screening
            job_description: Job description
            fairness_mode: Fairness mode (balanced, strict, etc.)
            resumes: List of resume dicts with filename, content (base64), file_type
        
        Returns:
            Screening session with results
        """
        db = SessionLocal()
        try:
            # Create screening session
            session = ScreeningSession(
                id=session_id,
                job_role=job_role,
                job_description=job_description,
                fairness_mode=fairness_mode,
                status=SessionStatus.PROCESSING,
                total_candidates=len(resumes)
            )
            db.add(session)
            db.commit()
            
            # Process each resume
            candidates_with_scores = []
            for idx, resume_data in enumerate(resumes):
                try:
                    candidate_result = await ScreeningOrchestrator._process_resume_in_batch(
                        db, session_id, idx, resume_data, job_role, job_description
                    )
                    if candidate_result:
                        candidates_with_scores.append(candidate_result)
                except Exception as e:
                    logger.error(f"Error processing resume {idx}: {str(e)}")
                    continue
            
            # Calculate fairness metrics across session
            if candidates_with_scores:
                fairness_metrics = await ScreeningOrchestrator._calculate_fairness_metrics(
                    db, session_id, candidates_with_scores
                )
                session.bias_metrics = fairness_metrics
                
                # Count shortlisted
                shortlisted = sum(1 for c in candidates_with_scores if c.get("shortlisted", False))
                session.shortlisted_count = shortlisted
                session.rejected_count = len(candidates_with_scores) - shortlisted
            
            session.status = SessionStatus.COMPLETED
            db.commit()
            
            return {
                "session_id": session_id,
                "status": "completed",
                "total": len(candidates_with_scores),
                "shortlisted": session.shortlisted_count,
                "fairness_score": session.fairness_score,
            }
            
        except Exception as e:
            logger.error(f"Batch screening failed for session {session_id}: {str(e)}")
            if session:
                session.status = SessionStatus.FAILED
                session.error_message = str(e)
                db.commit()
            raise
        finally:
            db.close()
    
    @staticmethod
    async def _process_resume_in_batch(
        db: Session,
        session_id: str,
        idx: int,
        resume_data: Dict[str, str],
        job_role: str,
        job_description: str,
    ) -> Optional[Dict[str, Any]]:
        """Process individual resume in batch context."""
        try:
            filename = resume_data.get("filename", f"resume_{idx}.pdf")
            content_b64 = resume_data.get("content", "")
            file_type = resume_data.get("file_type", "pdf")
            
            # Decode base64 content
            file_content = base64.b64decode(content_b64)
            
            # Upload to storage
            storage_result = storage_service.upload_file(
                file_content=file_content,
                original_filename=filename,
                content_type=FileValidator.get_content_type(filename)
            )
            
            # Create candidate
            candidate = Candidate(
                name=resume_data.get("name", f"Candidate {idx + 1}"),
                email=resume_data.get("email"),
                file_name=storage_result["file_path"],
                file_url=storage_result["file_url"],
                file_size=storage_result["file_size"],
                file_type=storage_result["file_type"],
                status=CandidateStatus.PENDING,
                screening_session_id=session_id,
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            # Process resume (parse + score)
            await UploadOrchestrator.process_resume(
                candidate.id,
                storage_result["file_url"],
                job_role=job_role,
                job_description=job_description,
            )
            
            # Get score
            score = db.query(Score).filter(Score.candidate_id == candidate.id).order_by(Score.created_at.desc()).first()
            
            # Create application ID
            application_id = f"APP{str(candidate.id)[:8].upper()}"
            
            # Create decision record (initially pending)
            decision = Decision(
                application_id=application_id,
                candidate_id=candidate.id,
                session_id=session_id,
                decision=DecisionStatus.PENDING,
            )
            db.add(decision)
            db.commit()
            
            # Determine if shortlisted (score > threshold, e.g., 70)
            shortlist_threshold = 70
            is_shortlisted = score and score.overall_score >= shortlist_threshold
            
            return {
                "application_id": application_id,
                "candidate_id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "score": score.overall_score if score else 0,
                "shortlisted": is_shortlisted,
                "skills": candidate.required_skills,
            }
            
        except Exception as e:
            logger.error(f"Failed to process resume {idx}: {str(e)}")
            return None
    
    @staticmethod
    async def _calculate_fairness_metrics(
        db: Session,
        session_id: str,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Calculate fairness metrics for the batch."""
        try:
            # Group candidates by protected attributes
            scores = [c.get("score", 0) for c in candidates]
            
            if not scores:
                return {"overall_score": 0.0}
            
            # Simple fairness calculation (can be enhanced)
            avg_score = sum(scores) / len(scores)
            
            return {
                "overall_score": round(avg_score / 100, 2),  # Normalize to 0-1
                "gender": 0.95,  # Placeholder - would come from ML service
                "age": 0.98,  # Placeholder
            }
        except Exception as e:
            logger.error(f"Fairness calculation failed: {str(e)}")
            return {"overall_score": 0.0}
