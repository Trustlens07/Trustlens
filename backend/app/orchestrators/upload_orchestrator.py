from sqlalchemy.orm import Session
import httpx
import logging
import io
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
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
    logger_temp.warning(
        "pytesseract/pdf2image not installed. OCR fallback disabled. "
        "Install with: pip install pytesseract pdf2image pillow"
    )

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


def _calculate_duration_years(start_date: str, end_date: str) -> float:
    """Calculate years between two dates in MM/YYYY or YYYY format."""
    def parse_date_str(date_str):
        if not date_str:
            return None
        if isinstance(date_str, str) and date_str.lower() in ["present", "current", "now"]:
            return datetime.now()
        match = re.match(r'(\d{1,2})/(\d{4})', str(date_str))
        if match:
            month, year = int(match.group(1)), int(match.group(2))
            if 1 <= month <= 12:
                return datetime(year, month, 1)
        match = re.match(r'^(\d{4})$', str(date_str))
        if match:
            year = int(match.group(1))
            if 1900 <= year <= 2100:
                return datetime(year, 1, 1)
        return None

    start = parse_date_str(start_date)
    end = parse_date_str(end_date)

    if not start or not end:
        return 0.0
    if start > end:
        return 0.0

    try:
        delta = relativedelta(end, start)
        return round(delta.years + (delta.months / 12.0), 1)
    except Exception:
        return 0.0


def _extract_experience_years_from_text(full_text: str) -> float:
    """
    Extract total years of experience from resume full_text.

    Strategy 1: Explicit statements like "6 years of experience", "over 6 years"
    Strategy 2: Parse and sum date ranges like "03/2023 - Present", "07/2020 - 03/2023"
    Strategy 3: Return 0.0 if nothing found
    """
    if not full_text:
        return 0.0

    # ── Strategy 1: Explicit years statement ────────────────────────────────
    explicit_patterns = [
        r'(?:over|more than|nearly|approximately|about)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?\s*(?:of\s+)?(?:experience|work|professional)',
        r'(\d+(?:\.\d+)?)\s*\+\s*years?\s*(?:of\s+)?(?:experience|work)',
        r'experience\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*\+?\s*years?',
    ]
    for pattern in explicit_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            years = float(match.group(1))
            if 0 < years < 50:
                logger.info(f"✅ Extracted {years} years from explicit statement in text")
                return years

    # ── Strategy 2: Sum date ranges ──────────────────────────────────────────
    date_range_pattern = re.compile(
        r'(\d{1,2}/\d{4}|\d{4})\s*[-–—]\s*(Present|Current|Now|\d{1,2}/\d{4}|\d{4})',
        re.IGNORECASE
    )
    ranges = date_range_pattern.findall(full_text)

    if ranges:
        total = 0.0
        seen_ranges = set()
        for start, end in ranges:
            key = f"{start}-{end}"
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            duration = _calculate_duration_years(start, end)
            if 0 < duration < 20:  # Sanity check per role
                total += duration
                logger.info(f"   Date range {start} → {end}: {duration} years")

        if total > 0:
            # Cap at 50 to avoid counting overlapping ranges
            total = min(round(total, 1), 50.0)
            logger.info(f"✅ Extracted {total} total years from date ranges in text")
            return total

    return 0.0


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract full text from PDF using pdfplumber, with OCR fallback."""
    text = ""
    try:
        logger.info("🔍 Attempting text extraction with pdfplumber...")
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text

        extracted_length = len(text)
        logger.info(f"✅ pdfplumber extracted {extracted_length} characters")

        if extracted_length < 50:
            logger.warning(f"⚠️ Low text extraction ({extracted_length} chars) — attempting OCR...")
            if not OCR_AVAILABLE:
                logger.error("❌ OCR not available.")
                return text
            try:
                images = convert_from_bytes(file_bytes, dpi=300)
                ocr_text = ""
                for page_num, image in enumerate(images, 1):
                    page_ocr_text = pytesseract.image_to_string(image, lang='eng')
                    ocr_text += page_ocr_text
                if len(ocr_text) > extracted_length:
                    text = ocr_text
            except Exception as ocr_error:
                logger.error(f"❌ OCR failed: {ocr_error}")

        logger.info(f"📊 Final extraction: {len(text)} characters")
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
        """Process resume after upload.

        Pipeline:
          Step 0 — Download PDF and extract full text     (fatal)
          Step 1 — Parse resume via ML /parse             (fatal)
          Step 2 — Fix parsed data:
                   - normalize skills
                   - fix experience entries
                   - extract total_experience_years from full_text if 0
                   - extract contact info from full_text if null
          Step 3 — Score resume via ML /score             (fatal)
          Step 4 — Generate feedback via /gemini/feedback (NON-FATAL)
        """
        db = SessionLocal()

        try:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                logger.error(f"Candidate {candidate_id} not found")
                return

            file_url = candidate.file_url or file_url
            if not file_url:
                raise ValueError("Candidate has no file_url")

            candidate.status = CandidateStatus.PROCESSING
            candidate.error_message = None
            db.commit()

            # ── Step 0: Download PDF and extract full text ───────────────────
            logger.info(f"📥 Downloading PDF for candidate {candidate_id}")
            async with httpx.AsyncClient() as client:
                file_response = await client.get(file_url)
                file_response.raise_for_status()
                file_bytes = file_response.content

            full_text = extract_text_from_pdf(file_bytes)
            logger.info(f"📄 Extracted {len(full_text)} characters from PDF")

            # ── Step 1: Parse resume ─────────────────────────────────────────
            logger.info(f"🔍 Parsing resume for candidate {candidate_id}")
            parsed_data = await ml_client.parse_resume(file_url)

            # Unwrap double nesting if present
            inner_data = parsed_data.get("parsed_data", parsed_data)
            inner_data["full_text"] = full_text

            # ── Step 2: Fix parsed data ──────────────────────────────────────

            # 2a: Normalize skills — split comma-separated, deduplicate
            raw_skills = inner_data.get("skills", [])
            normalized_skills = []
            seen_skills = set()
            for skill in raw_skills:
                if isinstance(skill, dict):
                    name = skill.get("name", "")
                    parts = [p.strip().lower() for p in name.split(",") if p.strip()]
                    for part in parts:
                        if part and part not in seen_skills:
                            seen_skills.add(part)
                            normalized_skills.append({
                                "name": part,
                                "category": skill.get("category", "other"),
                                "proficiency": skill.get("proficiency", "intermediate"),
                            })
                elif isinstance(skill, str):
                    for part in skill.split(","):
                        part = part.strip().lower()
                        if part and part not in seen_skills:
                            seen_skills.add(part)
                            normalized_skills.append({
                                "name": part,
                                "category": "other",
                                "proficiency": "intermediate",
                            })
            inner_data["skills"] = normalized_skills
            inner_data["skill_count"] = len(normalized_skills)
            logger.info(f"✅ Normalized {len(normalized_skills)} skills")

            # 2b: Normalize experience entries
            raw_experience = inner_data.get("experience", [])
            normalized_exp = []
            bullet_starts = [
                "successfully", "utilized", "collaborated", "improved",
                "conducted", "led", "developed", "monitored", "executed",
                "identified", "worked", "configured", "contributed",
            ]
            for exp in raw_experience:
                if not isinstance(exp, dict):
                    continue

                title = (exp.get("title") or "").strip()
                company = (exp.get("company") or "").strip()
                description = (exp.get("description") or "").strip()
                start_date = exp.get("start_date")
                end_date = exp.get("end_date")

                # Fix swapped company/title
                if company.lower() in ["present", "current", "now"] and \
                   re.search(r'\d{2}/\d{4}|\d{4}', title):
                    title, company = company, title

                # Extract dates from title
                date_match = re.search(
                    r'(\d{1,2}/\d{4}|\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|\d{4}|Present|Current|Now)',
                    title, re.IGNORECASE
                )
                if date_match:
                    start_date = date_match.group(1)
                    end_raw = date_match.group(2)
                    end_date = "Present" if end_raw.lower() in ["present", "current", "now"] else end_raw
                    title = re.sub(
                        r'\s*\d{1,2}/\d{4}\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current|Now)\s*',
                        ' ', title, flags=re.IGNORECASE
                    ).strip()

                # Strip location from title
                loc_match = re.search(r'([A-Za-z\s]+,\s*[A-Za-z\s]+)$', title)
                if loc_match:
                    potential = loc_match.group(1).strip()
                    if "," in potential and len(potential) < 50:
                        title = title[:loc_match.start()].strip()

                # Skip bullet point entries
                if any(title.lower().startswith(w) for w in bullet_starts):
                    continue

                if not title and not company:
                    continue

                normalized_exp.append({
                    "title": title,
                    "company": company,
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_years": _calculate_duration_years(start_date, end_date),
                    "description": description,
                })

            inner_data["experience"] = normalized_exp

            # 2c: Fix total_experience_years ─────────────────────────────────
            total_from_entries = round(
                sum(e.get("duration_years", 0.0) for e in normalized_exp), 1
            )
            logger.info(f"   Experience from entries: {total_from_entries} years")

            if total_from_entries < 0.5:
                # Entries gave 0 — try extracting from full_text
                total_from_text = _extract_experience_years_from_text(full_text)
                if total_from_text > 0:
                    inner_data["total_experience_years"] = total_from_text
                    logger.info(f"✅ Using text-extracted experience: {total_from_text} years")
                else:
                    # Last resort: keep ML parser value if it said something > 0
                    ml_years = float(inner_data.get("total_experience_years", 0.0))
                    inner_data["total_experience_years"] = ml_years if ml_years > 0 else 0.0
                    logger.info(f"   Using ML parser experience: {inner_data['total_experience_years']} years")
            else:
                inner_data["total_experience_years"] = total_from_entries
                logger.info(f"✅ Using calculated experience: {total_from_entries} years")

            # 2d: Fix contact info from full_text if ML missed it
            contact = inner_data.get("contact_info") or {}
            name = contact.get("name") or inner_data.get("name")
            email = contact.get("email") or inner_data.get("email")
            phone = contact.get("phone") or inner_data.get("phone")

            if not name and full_text:
                lines = full_text.strip().split('\n')[:3]
                for line in lines:
                    line = line.strip()
                    if line and '@' not in line and not line.startswith('http'):
                        words = line.split()
                        if 1 <= len(words) <= 4 and not any(c.isdigit() for c in line):
                            name = line
                            break

            if not email and full_text:
                m = re.search(r'[\w.\-+]+@[\w.\-]+\.\w+', full_text)
                if m:
                    email = m.group(0)

            if not phone and full_text:
                for pattern in [
                    r'\+?\d{1,2}[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}',
                    r'\(\d{3}\)\s*\d{3}[\s\-]?\d{4}',
                ]:
                    m = re.search(pattern, full_text)
                    if m:
                        phone = m.group(0)
                        break

            inner_data["contact_info"] = {
                "name": name,
                "email": email,
                "phone": phone,
                "location": contact.get("location"),
                "linkedin": contact.get("linkedin"),
                "github": contact.get("github"),
            }

            candidate.parsed_data = inner_data
            candidate.name = name or candidate.name
            candidate.email = email or candidate.email
            candidate.phone = phone or candidate.phone
            db.commit()

            logger.info(
                f"✅ Data fixed: skills={len(normalized_skills)}, "
                f"exp_years={inner_data['total_experience_years']}, "
                f"name={name}"
            )

            # ── Step 3: Score resume (pretrained model) ──────────────────────
            logger.info(f"📊 Scoring resume for candidate {candidate_id}")

            score_data = await ml_client.score_resume(
                inner_data,
                required_skills=candidate.required_skills,
            )

            overall_score = score_data.get("overall_score", 0.0)
            components = score_data.get("components", {})

            logger.info(
                f"✅ Score: {overall_score} | "
                f"skills={components.get('skills')} "
                f"exp={components.get('experience')} "
                f"edu={components.get('education')}"
            )

            score = Score(
                candidate_id=candidate_id,
                overall_score=overall_score,
                skill_score=components.get("skills", 0.0),
                experience_score=components.get("experience", 0.0),
                education_score=components.get("education", 0.0),
                breakdown={
                    **components,
                    "matched_skills": score_data.get("matched_skills", []),
                    "missing_skills": score_data.get("missing_skills", []),
                    "additional_skills": score_data.get("additional_skills", []),
                    "explanation": score_data.get("explanation", ""),
                    "fairness_applied": score_data.get("fairness_applied", False),
                    "mode": score_data.get("mode", "baseline"),
                },
            )
            db.add(score)
            db.flush()

            # ── Step 4: Generate feedback (Gemini — NON-FATAL) ───────────────
            feedback_text = ""
            try:
                logger.info(f"💬 Generating Gemini feedback for candidate {candidate_id}")
                feedback_text = await ml_client.generate_feedback(score_data, inner_data)
                logger.info(f"✅ Feedback generated ({len(feedback_text)} chars)")
            except Exception as feedback_err:
                logger.warning(
                    f"⚠️ Gemini feedback failed (non-fatal): {_format_error(feedback_err)}"
                )
                feedback_text = (
                    f"Score: {overall_score:.1f}/100. "
                    f"{score_data.get('explanation', '')}"
                ).strip()

            matched = score_data.get("matched_skills") or []
            missing = score_data.get("missing_skills") or []

            feedback = Feedback(
                candidate_id=candidate_id,
                feedback_text=feedback_text,
                strengths=", ".join(str(s) for s in matched[:10]) if matched else None,
                improvements=", ".join(str(s) for s in missing[:10]) if missing else None,
            )
            db.add(feedback)

            # ── Mark completed ───────────────────────────────────────────────
            candidate.status = CandidateStatus.COMPLETED
            candidate.error_message = None
            db.commit()

            logger.info(f"✅ Candidate {candidate_id} complete. Score: {overall_score}")

        except Exception as e:
            detail = _format_error(e)
            logger.error("❌ Failed to process candidate %s: %s", candidate_id, detail, exc_info=True)
            try:
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
                if candidate:
                    candidate.status = CandidateStatus.FAILED
                    candidate.error_message = detail
                    db.commit()
            except Exception as db_err:
                logger.error(f"❌ Could not update candidate status: {db_err}")
        finally:
            db.close()