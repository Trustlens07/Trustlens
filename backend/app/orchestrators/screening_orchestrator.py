import asyncio
import logging
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

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
    ) -> Dict[str, Any]:
        """Calculate actual fairness metrics for the batch using statistical measures."""
        try:
            if not candidates:
                return {"overall_score": 0.0, "total_candidates": 0}
            
            # Extract all scores
            all_scores = [c.get("score", 0) for c in candidates if c.get("score") is not None]
            if not all_scores:
                return {"overall_score": 0.0, "total_candidates": len(candidates)}
            
            # Calculate basic statistics
            overall_mean = sum(all_scores) / len(all_scores)
            overall_std = (sum((x - overall_mean) ** 2 for x in all_scores) / len(all_scores)) ** 0.5
            
            # Group candidates by protected attributes (extract from parsed data or use provided)
            scores_by_group = {"overall": all_scores}
            
            # Try to extract gender/age groups from candidate data
            for candidate in candidates:
                score = candidate.get("score", 0)
                parsed_data = candidate.get("parsed_data", {})
                
                # Extract name to infer gender (simple heuristic - can be enhanced)
                name = candidate.get("name", "")
                if name:
                    # Simple first-name based grouping (production would use proper NLP)
                    gender_group = ScreeningOrchestrator._infer_gender_from_name(name)
                    if gender_group:
                        scores_by_group.setdefault(f"gender_{gender_group}", []).append(score)
            
            # Calculate Demographic Parity: Are groups receiving similar average scores?
            group_means = {}
            for group, scores in scores_by_group.items():
                if len(scores) > 0:
                    group_means[group] = sum(scores) / len(scores)
            
            # Calculate Demographic Parity Ratio (min mean / max mean)
            # Closer to 1.0 = more fair
            mean_values = list(group_means.values())
            if len(mean_values) >= 2:
                max_mean = max(mean_values)
                min_mean = min(mean_values)
                demographic_parity_ratio = min_mean / max_mean if max_mean > 0 else 0.0
            else:
                demographic_parity_ratio = 1.0  # Default if only one group
            
            # Calculate Equal Opportunity Difference (max diff from overall mean)
            if len(mean_values) >= 2:
                equal_opportunity_diff = max(abs(m - overall_mean) for m in mean_values)
            else:
                equal_opportunity_diff = 0.0
            
            # Calculate disparate impact (80% rule)
            # A group is adversely impacted if their selection rate is < 80% of the highest
            selection_threshold = 70  # Score threshold for "selected"
            selection_rates = {}
            for group, scores in scores_by_group.items():
                if len(scores) > 0:
                    selected = sum(1 for s in scores if s >= selection_threshold)
                    selection_rates[group] = selected / len(scores)
            
            if len(selection_rates) >= 2:
                max_selection = max(selection_rates.values())
                disparate_impact_scores = {
                    group: (rate / max_selection if max_selection > 0 else 0.0)
                    for group, rate in selection_rates.items()
                }
            else:
                disparate_impact_scores = {}
            
            # Determine if bias is detected (using 0.8 disparate impact threshold)
            is_biased = any(
                ratio < 0.8 for ratio in disparate_impact_scores.values()
            ) if disparate_impact_scores else False
            
            # Calculate overall fairness score (composite metric)
            fairness_components = [
                demographic_parity_ratio,  # 0-1 scale
                1.0 - min(equal_opportunity_diff / 20, 1.0),  # Normalize to 0-1
            ]
            overall_fairness = sum(fairness_components) / len(fairness_components)
            
            metrics = {
                "overall_score": round(overall_fairness, 3),
                "total_candidates": len(candidates),
                "mean_score": round(overall_mean, 2),
                "std_deviation": round(overall_std, 2),
                "demographic_parity_ratio": round(demographic_parity_ratio, 3),
                "equal_opportunity_diff": round(equal_opportunity_diff, 2),
                "group_means": {k: round(v, 2) for k, v in group_means.items()},
                "selection_rates": {k: round(v, 3) for k, v in selection_rates.items()},
                "disparate_impact": disparate_impact_scores,
                "is_biased": is_biased,
                "bias_detected_groups": [
                    group for group, ratio in disparate_impact_scores.items()
                    if ratio < 0.8
                ],
                "recommendations": ScreeningOrchestrator._generate_fairness_recommendations(
                    is_biased, demographic_parity_ratio, disparate_impact_scores
                ),
                "calculation_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Fairness metrics calculated for session {session_id}: {metrics['overall_score']}")
            return metrics
            
        except Exception as e:
            logger.error(f"Fairness calculation failed: {str(e)}", exc_info=True)
            return {
                "overall_score": 0.0,
                "total_candidates": len(candidates) if candidates else 0,
                "error": str(e)
            }
    
    @staticmethod
    def _infer_gender_from_name(name: str) -> Optional[str]:
        """Simple heuristic to infer gender from first name (for demo purposes)."""
        # This is a simplified approach - production should use proper NLP or allow manual input
        female_indicators = ['a', 'e', 'i', 'y']  # Common endings
        male_indicators = ['n', 'r', 'd', 's']
        
        first_name = name.split()[0].lower() if name else ""
        if not first_name:
            return None
        
        # Very naive heuristic for demonstration
        if first_name[-1] in female_indicators:
            return "female"
        elif first_name[-1] in male_indicators:
            return "male"
        return "unknown"
    
    @staticmethod
    def _generate_fairness_recommendations(
        is_biased: bool,
        demographic_parity_ratio: float,
        disparate_impact: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations based on fairness metrics."""
        recommendations = []
        
        if not is_biased:
            recommendations.append("No significant bias detected. Current scoring appears fair across groups.")
            return recommendations
        
        if demographic_parity_ratio < 0.9:
            recommendations.append(
                f"Demographic parity ratio is {demographic_parity_ratio:.2f}. "
                "Consider reviewing scoring criteria to ensure groups receive comparable scores."
            )
        
        biased_groups = [g for g, r in disparate_impact.items() if r < 0.8]
        if biased_groups:
            recommendations.append(
                f"Potential adverse impact detected for groups: {', '.join(biased_groups)}. "
                "Review selection threshold and ensure job requirements are truly necessary."
            )
        
        recommendations.append(
            "Consider implementing blind resume screening (removing names/gender indicators) "
            "before scoring to reduce unconscious bias."
        )
        
        recommendations.append(
            "Regularly monitor these metrics and establish an appeal process for candidates "
            "who may have been adversely affected."
        )
        
        return recommendations
