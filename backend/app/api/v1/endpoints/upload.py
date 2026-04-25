from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import timezone
import asyncio
import uuid
from app.core.database import get_db
from app.services.storage_service import storage_service
from app.services.ml_client import ml_client
from app.orchestrators.upload_orchestrator import UploadOrchestrator
from app.utils.file_validator import FileValidator
from app.models.candidate import Candidate, CandidateStatus
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    candidate_name: Optional[str] = Form(None),
    candidate_email: Optional[str] = Form(None),
    required_skills: Optional[str] = Form(None, description="Comma-separated list of skills to match against"),
    job_role: Optional[str] = Form(None, description="Job role for candidate report"),
    db: Session = Depends(get_db)
):
    """
    Upload a resume file
    
    Args:
        file: Resume PDF file
        candidate_name: Candidate name
        candidate_email: Candidate email
        required_skills: Comma-separated skills (e.g., "Python,JavaScript,AWS")
        job_role: Job role for candidate report (e.g., "Software Engineer")
    """
    try:
        # Validate file
        FileValidator.validate_file(file)
        
        # Read file content
        file_content = await file.read()
        content_type = FileValidator.get_content_type(file.filename)
        
        # Upload to storage
        storage_result = storage_service.upload_file(
            file_content=file_content,
            original_filename=file.filename,
            content_type=content_type
        )
        
        # Parse required_skills if provided
        skills_list = None
        if required_skills:
            skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
        
        # Generate unique application_id (format: APP-XXXXX)
        unique_suffix = str(uuid.uuid4())[:5].upper()
        application_id = f"APP-{unique_suffix}"
        
        # Create candidate record
        candidate = Candidate(
            name=candidate_name,
            email=candidate_email,
            file_name=storage_result["file_path"],
            file_url=storage_result["file_url"],
            file_size=storage_result["file_size"],
            file_type=storage_result["file_type"],
            status=CandidateStatus.PENDING,
            required_skills=skills_list,  # Store user-provided skills
            job_role=job_role,  # Store job role
            application_id=application_id,  # Store unique app ID
        )
        
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        # Process in background with error handling
        async def process_with_error_handling():
            """Wrapper that catches errors and updates candidate status"""
            try:
                await UploadOrchestrator.process_resume(
                    candidate.id,
                    storage_result["file_url"],
                    job_role=job_role,
                )
            except Exception as e:
                logger.error(f"Background processing failed for candidate {candidate.id}: {str(e)}")
                # Update candidate status to failed in case it wasn't already
                try:
                    from app.core.database import SessionLocal
                    db_err = SessionLocal()
                    cand = db_err.query(Candidate).filter(Candidate.id == candidate.id).first()
                    if cand and cand.status != CandidateStatus.FAILED:
                        cand.status = CandidateStatus.FAILED
                        cand.error_message = f"Background processing error: {str(e)[:500]}"
                        db_err.commit()
                    db_err.close()
                except Exception as db_err:
                    logger.error(f"Failed to update candidate status: {db_err}")
        
        # Schedule the wrapped coroutine
        asyncio.create_task(process_with_error_handling())
        
        uploaded_at = candidate.created_at
        if uploaded_at is not None:
            if uploaded_at.tzinfo is None:
                uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)
            uploaded_at = uploaded_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            uploaded_at = None
        
        return {
            "candidate_id": candidate.id,
            "application_id": application_id,
            "file_id": storage_result["file_path"],
            "filename": storage_result["original_name"],
            "size_bytes": storage_result["file_size"],
            "storage_url": storage_result["file_url"],
            "required_skills": skills_list,
            "job_role": job_role,
            "uploaded_at": uploaded_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/batch")
async def batch_upload(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    job_role: Optional[str] = Form(None, description="Job role for all candidates"),
    db: Session = Depends(get_db)
):
    """
    Upload multiple resume files
    
    Args:
        files: List of resume PDF files
        job_role: Optional job role for all candidates
    """
    uploaded_candidates = []
    failed_uploads = []
    
    for file in files:
        try:
            # Validate file
            FileValidator.validate_file(file)
            
            # Read file content
            file_content = await file.read()
            content_type = FileValidator.get_content_type(file.filename)
            
            # Upload to storage
            storage_result = storage_service.upload_file(
                file_content=file_content,
                original_filename=file.filename,
                content_type=content_type
            )
            
            # Generate unique application_id
            unique_suffix = str(uuid.uuid4())[:5].upper()
            application_id = f"APP-{unique_suffix}"
            
            # Create candidate record
            candidate = Candidate(
                file_name=storage_result["file_path"],
                file_url=storage_result["file_url"],
                file_size=storage_result["file_size"],
                file_type=storage_result["file_type"],
                status=CandidateStatus.PENDING,
                job_role=job_role,
                application_id=application_id,
            )
            
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            uploaded_candidates.append({
                "candidate_id": candidate.id,
                "application_id": application_id,
                "file_name": storage_result["original_name"],
                "job_role": job_role
            })
            
            # Process in background (see note in single upload).
            asyncio.create_task(
                UploadOrchestrator.process_resume(
                    candidate.id,
                    storage_result["file_url"],
                )
            )
            
        except Exception as e:
            failed_uploads.append({
                "file_name": file.filename,
                "error": str(e)
            })
    
    return {
        "success": True,
        "message": f"Uploaded {len(uploaded_candidates)} files",
        "data": {
            "uploaded": uploaded_candidates,
            "failed": failed_uploads
        }
    }