from sqlalchemy.orm import Session
import httpx
import logging
import io
import pdfplumber
from tenacity import RetryError

# OCR imports
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("pytesseract/pdf2image not installed. OCR fallback disabled. Install with: pip install pytesseract pdf2image pillow")

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

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract full text from PDF using pdfplumber, with OCR fallback for scanned PDFs.
    
    Flow:
    1. Try pdfplumber (fast, for digital PDFs)
    2. If < 50 chars extracted, try OCR with Tesseract (for scanned/image PDFs)
    3. Return whatever text was extracted
    """
    text = ""
    
    try:
        # Step 1: Try pdfplumber (works for searchable/digital PDFs)
        logger.info("🔍 Attempting text extraction with pdfplumber...")
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
        
        extracted_length = len(text)
        logger.info(f"✅ pdfplumber extracted {extracted_length} characters")
        
        # Step 2: If text is minimal, try OCR as fallback
        if extracted_length < 50:
            logger.warning(f"⚠️ Low text extraction ({extracted_length} chars) - attempting OCR fallback...")
            
            if not OCR_AVAILABLE:
                logger.error("❌ OCR not available. Install: pip install pytesseract pdf2image pillow")
                return text  # Return whatever pdfplumber got
            
            try:
                logger.info("🔄 Converting PDF to images for OCR...")
                images = convert_from_bytes(file_bytes, dpi=300)
                logger.info(f"📄 Converted to {len(images)} image(s), running Tesseract OCR...")
                
                ocr_text = ""
                for page_num, image in enumerate(images, 1):
                    logger.info(f"🔤 OCR on page {page_num}/{len(images)}...")
                    page_ocr_text = pytesseract.image_to_string(image, lang='eng')
                    ocr_text += page_ocr_text
                    if page_ocr_text.strip():
                        logger.info(f"   ✓ Page {page_num}: {len(page_ocr_text)} chars extracted via OCR")
                
                ocr_length = len(ocr_text)
                if ocr_length > extracted_length:
                    logger.info(f"✅ OCR improved extraction: {extracted_length} → {ocr_length} characters")
                    text = ocr_text
                else:
                    logger.info(f"⚠️ OCR didn't improve results. Keeping pdfplumber text ({extracted_length} chars)")
                    
            except Exception as ocr_error:
                logger.error(f"❌ OCR failed: {ocr_error}. Continuing with pdfplumber extraction...")
                # Continue with whatever pdfplumber extracted
        
        final_length = len(text)
        logger.info(f"📊 Final extraction: {final_length} characters")
        return text
        
    except Exception as e:
        logger.error(f"❌ PDF extraction failed: {e}", exc_info=True)
        return ""

class UploadOrchestrator:
    @staticmethod
    async def process_resume(
        candidate_id: str,
        file_url: str,
        job_role: str = None,
        job_description: str = None,
    ):
        """Process resume after upload
        
        Args:
            candidate_id: ID of the candidate
            file_url: URL of the resume file
            job_role: Optional job role for context-aware scoring
            job_description: Optional job description for context-aware scoring
        """
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
            
            # Step 0: Extract full text from PDF
            logger.info(f"Extracting full text from PDF for candidate {candidate_id}")
            async with httpx.AsyncClient() as client:
                file_response = await client.get(file_url)
                file_response.raise_for_status()
                file_bytes = file_response.content
                logger.info(f"Downloaded PDF size: {len(file_bytes)} bytes")
                logger.info(f"First 200 bytes: {file_bytes[:200]}")
                full_text = extract_text_from_pdf(file_bytes)
                logger.info(f"Extracted {len(full_text)} characters from PDF")

            # Step 1: Parse resume
            logger.info(f"Parsing resume for candidate {candidate_id}")
            parsed_data = await ml_client.parse_resume(file_url)
            logger.info(f"📄 Parse response keys: {list(parsed_data.keys())}")

            # Update candidate with parsed data and full text
            logger.info(f"📝 Adding full_text ({len(full_text)} chars) to parsed_data")
            parsed_data["full_text"] = full_text
            candidate.parsed_data = parsed_data
            candidate.name = parsed_data.get("name", candidate.name)
            candidate.email = parsed_data.get("email", candidate.email)
            candidate.phone = parsed_data.get("phone", candidate.phone)
            db.commit()
            
            # Step 2: Score resume
            logger.info(f"Scoring resume for candidate {candidate_id}")
            logger.info(f"📋 Candidate required_skills: {candidate.required_skills}")
            # Use user-provided skills if available, otherwise ml_client will auto-extract
            score_data = await ml_client.score_resume(
                parsed_data, 
                required_skills=candidate.required_skills
            )

            # Save scores
            # score_data now contains standardized keys: "overall_score" and "components"
            overall_score = score_data.get("overall_score", 0.0)
            components = score_data.get("components", {})
            skill_score = components.get("skills", 0.0)
            experience_score = components.get("experience", 0.0)
            education_score = components.get("education", 0.0)

            score = Score(
                candidate_id=candidate_id,
                overall_score=overall_score,
                skill_score=skill_score,
                experience_score=experience_score,
                education_score=education_score,
                breakdown=components,
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