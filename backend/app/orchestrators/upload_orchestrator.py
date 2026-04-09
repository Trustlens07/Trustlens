from sqlalchemy.orm import Session
import httpx
import logging
from tenacity import RetryError

from app.core.database import SessionLocal
from app.services.ml_client import ml_client
from app.models.candidate import Candidate, CandidateStatus
from app.models.score import Score
from app.models.feedback import Feedback

logger = logging.getLogger(__name__)

def _unwrap_error(exc: BaseException) -> BaseException:
    if isinstance(exc, RetryError):
        fut = exc.last_attempt
        try:
            inner = fut.exception()
            if inner is not None:
                return inner
        except Exception:
            return exc
    return exc

def _format_error(exc: BaseException) -> str:
    e = _unwrap_error(exc)
    if isinstance(e, httpx.HTTPStatusError):
        body = (e.response.text or "").strip().replace("\n", " ")
        if len(body) > 400:
            body = body[:400] + "…"
        return f"HTTP {e.response.status_code} from {e.request.method} {e.request.url} — {body}"
    if isinstance(e, httpx.RequestError):
        return f"HTTP request error: {e}"
    return str(e)

class UploadOrchestrator:
    @staticmethod
    async def process_resume(candidate_id: str, file_url: str):
        """Process resume after upload"""
        db = SessionLocal()
        
        try:
            # Update status to processing
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                logger.error(f"Candidate {candidate_id} not found")
                return

            # Always prefer DB URL (may differ from passed argument)
            file_url = candidate.file_url or file_url
            if not file_url:
                raise ValueError("Candidate has no file_url")

            candidate.status = CandidateStatus.PROCESSING
            candidate.error_message = None
            db.commit()
            
            # Step 1: Parse resume
            logger.info(f"Parsing resume for candidate {candidate_id}")
            parsed_data = await ml_client.parse_resume(file_url)
            
            # Update candidate with parsed data
            candidate.parsed_data = parsed_data
            candidate.name = parsed_data.get("name", candidate.name)
            candidate.email = parsed_data.get("email", candidate.email)
            candidate.phone = parsed_data.get("phone", candidate.phone)
            db.commit()
            
            # Step 2: Score resume
            logger.info(f"Scoring resume for candidate {candidate_id}")
            score_data = await ml_client.score_resume(parsed_data)
            
            # Save scores
            # Map ML score response shape to DB model
            components = score_data.get("components") or {}
            overall_score = score_data.get("total_score", score_data.get("overall_score", 0.0))
            skill_score = components.get("skill_score", components.get("skill", 0.0))
            experience_score = components.get("experience_score", components.get("experience", 0.0))
            education_score = components.get("education_score", components.get("education", 0.0))

            score = Score(
                candidate_id=candidate_id,
                overall_score=overall_score,
                skill_score=skill_score,
                experience_score=experience_score,
                education_score=education_score,
                breakdown=components if components else score_data,
            )
            db.add(score)
            
            # Step 3: Generate feedback
            logger.info(f"Generating feedback for candidate {candidate_id}")
            feedback_text = await ml_client.generate_feedback(score_data, parsed_data)

            strengths = score_data.get("strengths")
            improvements = score_data.get("improvements")
            # If ML doesn't provide these fields, derive lightweight text from skills lists.
            if strengths is None:
                matched = score_data.get("matched_skills") or []
                if isinstance(matched, list) and matched:
                    strengths = ", ".join(str(s) for s in matched[:10])
            if improvements is None:
                missing = score_data.get("missing_skills") or []
                if isinstance(missing, list) and missing:
                    improvements = ", ".join(str(s) for s in missing[:10])

            feedback = Feedback(
                candidate_id=candidate_id,
                feedback_text=feedback_text,
                strengths=strengths,
                improvements=improvements,
            )
            db.add(feedback)
            
            # Update status to completed
            candidate.status = CandidateStatus.COMPLETED
            db.commit()
            
            logger.info(f"Successfully processed candidate {candidate_id}")
            
        except Exception as e:
            detail = _format_error(e)
            logger.error("Failed to process candidate %s: %s", candidate_id, detail, exc_info=True)
            if db:
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
                if candidate:
                    candidate.status = CandidateStatus.FAILED
                    candidate.error_message = detail
                    db.commit()
        finally:
            db.close()