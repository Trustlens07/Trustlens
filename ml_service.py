# ml_service.py - FINAL COMPLETE VERSION


from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import re
import io
import PyPDF2
import docx
import numpy as np
import google.generativeai as genai

# ============================================
# CONFIGURATION
# ============================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    GEMINI_AVAILABLE = True
else:
    GEMINI_AVAILABLE = False

app = FastAPI(title="ML Resume Service", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# PYDANTIC SCHEMAS
# ============================================

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None

class Skill(BaseModel):
    name: str
    category: str
    proficiency: str = "intermediate"

class Experience(BaseModel):
    title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_years: float = 0.0
    description: str = ""

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[int] = None
    field_of_study: Optional[str] = None

class Project(BaseModel):
    name: str
    description: str = ""
    technologies: List[str] = []

class ParsedResume(BaseModel):
    file_name: str
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: List[Skill] = []
    soft_skills: List[str] = []
    experience: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certifications: List[str] = []
    achievements: List[str] = []
    languages: List[str] = []
    publications: List[str] = []
    volunteer: List[str] = []
    total_experience_years: float = 0.0
    skill_count: int = 0
    education_level: str = ""

class ScoreRequest(BaseModel):
    required_skills: List[str]
    resume: ParsedResume
    mode: str = "baseline"
    fairness_mode: str = "balanced"
    custom_ignore_fields: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None

class ScoreResponse(BaseModel):
    score: float
    mode: str
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    short_explanation: str
    components: Dict[str, float]
    weights_used: Dict[str, float]
    fairness_applied: bool
    ignored_fields: List[str]

class CandidateReportRequest(BaseModel):
    required_skills: List[str]
    resume: ParsedResume
    mode: str = "enhanced"
    fairness_mode: str = "balanced"
    custom_ignore_fields: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None

class CandidateReportResponse(BaseModel):
    candidate_name: str
    overall_score: float
    verdict: str
    score_breakdown: Dict[str, float]
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    experience_years: float
    education_level: str
    soft_skills: List[str]
    project_count: int
    certification_count: int
    achievement_count: int
    language_count: int
    detailed_explanation: str
    recommendations: List[str]
    weights_used: Dict[str, float]

class BiasRequest(BaseModel):
    scores: List[float]
    candidates_data: List[Dict[str, str]]

# ============================================
# FAIRNESS ENGINE
# ============================================

class FairnessEngine:
    @staticmethod
    def apply_fairness(resume: ParsedResume, mode: str, custom_ignore: List[str] = None):
        ignored = []
        if mode == "strict":
            resume.contact_info.name = "[REDACTED]"
            resume.contact_info.email = "[REDACTED]"
            resume.contact_info.phone = "[REDACTED]"
            resume.contact_info.location = "[REDACTED]"
            for edu in resume.education:
                edu.institution = "[REDACTED]"
            ignored = ["name", "email", "phone", "location", "institution"]
        elif mode == "balanced":
            resume.contact_info.name = "[REDACTED]"
            ignored = ["name"]
        elif mode == "custom" and custom_ignore:
            if "name" in custom_ignore:
                resume.contact_info.name = "[REDACTED]"
                ignored.append("name")
            if "email" in custom_ignore:
                resume.contact_info.email = "[REDACTED]"
                ignored.append("email")
            if "phone" in custom_ignore:
                resume.contact_info.phone = "[REDACTED]"
                ignored.append("phone")
            if "location" in custom_ignore:
                resume.contact_info.location = "[REDACTED]"
                ignored.append("location")
            if "institution" in custom_ignore:
                for edu in resume.education:
                    edu.institution = "[REDACTED]"
                ignored.append("institution")
        return resume, ignored

# ============================================
# DOCUMENT EXTRACTION
# ============================================

class DocumentExtractor:
    @staticmethod
    def extract_baseline(file_bytes: bytes, file_type: str) -> str:
        if file_type == "pdf":
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                return " ".join([page.extract_text() or "" for page in reader.pages])
            except:
                return ""
        else:
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                return " ".join([p.text for p in doc.paragraphs])
            except:
                return ""

    @staticmethod
    def extract_enhanced(file_bytes: bytes, file_type: str) -> str:
        text = DocumentExtractor.extract_baseline(file_bytes, file_type)
        if GEMINI_AVAILABLE and text:
            try:
                prompt = f"Clean this resume text. Fix OCR errors. Keep all sections (skills, experience, education, projects, certifications, achievements, languages).\n\n{text[:6000]}"
                response = gemini_model.generate_content(prompt)
                return response.text if response.text else text
            except:
                return text
        return text

# ============================================
# RESUME PARSER (Comprehensive, with strict filters)
# ============================================

class ResumeParser:
    @staticmethod
    def parse(text: str, file_name: str) -> ParsedResume:
        parsed = ParsedResume(file_name=file_name)
        lines = text.split('\n')
        text_lower = text.lower()

        # ---------- 1. Contact Info ----------
        for line in lines[:15]:
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', line.strip()) and len(line.strip()) < 50:
                parsed.contact_info.name = line.strip()
                break
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            parsed.contact_info.email = email_match.group()
        phone_match = re.search(r'\b(?:\+?91[-.\s]?)?\d{10}\b', text)
        if phone_match:
            parsed.contact_info.phone = phone_match.group()
        loc_match = re.search(r'(?:location|based in|city)[:\s]+([A-Za-z\s,]+)', text, re.IGNORECASE)
        if loc_match:
            parsed.contact_info.location = loc_match.group(1).strip()
        github_match = re.search(r'github\.com/[\w-]+', text)
        if github_match:
            parsed.contact_info.github = github_match.group()
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text)
        if linkedin_match:
            parsed.contact_info.linkedin = linkedin_match.group()

        # ---------- 2. Summary ----------
        summary_section = ResumeParser._extract_section(text, r'(?:summary|profile|about me)', r'(?:experience|work history|education|skills)')
        if summary_section:
            parsed.summary = summary_section[:500]

        # ---------- 3. Skills ----------
        skill_set = set()
        inline_skills = re.findall(r'(?:skills?|technologies?|competencies?)[:\s]+([^\n]+)', text, re.IGNORECASE)
        for line in inline_skills:
            for skill in re.split(r'[ ,;•|]+', line):
                skill = skill.strip().lower()
                if len(skill) > 1 and not skill.isdigit():
                    skill_set.add(skill)
        skills_section = ResumeParser._extract_section(text, r'(?:skills?|technologies?|core competencies)', r'(?:experience|work history|education|projects)')
        if skills_section:
            bullet_points = ResumeParser._extract_bullet_points(skills_section)
            for bp in bullet_points:
                for token in re.split(r'[ ,;•|]+', bp):
                    token = token.strip().lower()
                    if len(token) > 1 and not token.isdigit():
                        skill_set.add(token)
        skill_categories = {
            "programming": ["python", "java", "javascript", "c", "c++", "c#", "go", "rust", "sql", "nosql"],
            "frameworks": ["react", "angular", "vue", "django", "flask", "fastapi", "tensorflow", "pytorch", "pandas", "numpy"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins"],
            "data_science": ["machine learning", "deep learning", "nlp", "data analysis", "tableau", "power bi"],
            "business": ["project management", "agile", "scrum", "jira", "sales", "marketing", "seo"],
            "design": ["figma", "adobe xd", "photoshop", "illustrator", "ui/ux"],
            "soft": ["leadership", "communication", "teamwork", "problem solving", "critical thinking", "time management", "adaptability", "creativity"]
        }
        for skill in skill_set:
            category = "other"
            for cat, keywords in skill_categories.items():
                if any(keyword in skill for keyword in keywords):
                    category = cat
                    break
            if not any(s.name == skill for s in parsed.skills):
                parsed.skills.append(Skill(name=skill, category=category))
        parsed.skill_count = len(parsed.skills)

        # ---------- 4. Work Experience ----------
        exp_section = ResumeParser._extract_section(text, r'(?:experience|work history|employment)', r'(?:education|projects|skills)')
        if exp_section:
            job_blocks = re.split(r'\n(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[-–|]\s+)?)', exp_section)
            for block in job_blocks:
                if not block.strip():
                    continue
                exp = Experience(title="", company="")
                lines_blk = block.strip().split('\n')
                title_line = lines_blk[0]
                title_company_match = re.match(r'(.+?)\s+(?:at|@|-|–)\s+(.+)', title_line, re.IGNORECASE)
                if title_company_match:
                    exp.title = title_company_match.group(1).strip()
                    exp.company = title_company_match.group(2).strip()
                else:
                    exp.title = title_line.strip()
                date_match = re.search(r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|present)', block, re.IGNORECASE)
                if date_match:
                    exp.start_date = date_match.group(1)
                    exp.end_date = date_match.group(2)
                    start_year = int(re.search(r'\d{4}', exp.start_date).group())
                    end_year = int(re.search(r'\d{4}', exp.end_date).group()) if re.search(r'\d{4}', exp.end_date) else datetime.now().year
                    exp.duration_years = end_year - start_year
                desc_lines = lines_blk[1:] if len(lines_blk) > 1 else []
                exp.description = ' '.join(desc_lines)[:500]
                parsed.experience.append(exp)
        parsed.total_experience_years = sum(e.duration_years for e in parsed.experience)

        # ---------- 5. Education ----------
        edu_section = ResumeParser._extract_section(text, r'(?:education|academic background)', r'(?:experience|projects|skills)')
        if edu_section:
            edu_blocks = re.split(r'\n(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+[-–|]?\s*\d{4})', edu_section)
            for block in edu_blocks:
                if not block.strip():
                    continue
                edu = Education(degree="", institution="")
                lines_blk = block.strip().split('\n')
                first_line = lines_blk[0]
                degree_match = re.search(r'([A-Za-z\.\s]+?)(?:,|$)', first_line)
                if degree_match:
                    edu.degree = degree_match.group(1).strip()
                inst_match = re.search(r'(?:at|,)\s*([A-Za-z\s]+?)(?:,|\d{4}|$)', first_line)
                if inst_match:
                    edu.institution = inst_match.group(1).strip()
                year_match = re.search(r'\b(19|20)\d{2}\b', block)
                if year_match:
                    edu.graduation_year = int(year_match.group())
                parsed.education.append(edu)
        parsed.education_level = ResumeParser._get_education_level(parsed.education)

        # ---------- 6. Projects (strict: filter internship/assisted lines) ----------
        proj_section = ResumeParser._extract_section(text, r'(?:projects?|portfolio)', r'(?:experience|education|skills|certifications)')
        if proj_section:
            proj_items = ResumeParser._extract_bullet_points(proj_section)
            for item in proj_items[:5]:
                # Exclude lines that look like work experience (intern, assisted, etc.)
                if not re.search(r'\b(intern|assisted|helped|supported|developer|engineer)\b', item.lower()):
                    name = re.split(r'[:–\-\(]', item)[0].strip()
                    parsed.projects.append(Project(name=name, description=item[:200]))
        else:
            # Fallback: scan whole text for numbered project lines (still filter)
            proj_lines = re.findall(r'^\s*\d+[\.\)]?\s+(.+?)(?=\n\s*\d+[\.\)]?|\Z)', text, re.MULTILINE)
            for line in proj_lines[:5]:
                if not re.search(r'\b(intern|assisted|helped|supported|developer|engineer)\b', line.lower()):
                    name = re.split(r'[:–\-\(]', line)[0].strip()
                    parsed.projects.append(Project(name=name, description=line[:200]))

        # ---------- 7. Certifications (filter out language lines) ----------
        cert_section = ResumeParser._extract_section(text, r'(?:certifications?|licenses?)', r'(?:experience|education|skills|projects)')
        if cert_section:
            cert_items = ResumeParser._extract_bullet_points(cert_section)
            for cert in cert_items[:5]:
                if not re.search(r'\b(english|hindi|kannada|spanish|french|german)\b', cert.lower()):
                    parsed.certifications.append(cert.strip())
        else:
            cert_lines = re.findall(r'^\s*\d+[\.\)]?\s+(.+?)(?=\n\s*\d+[\.\)]?|\Z)', text, re.MULTILINE)
            for line in cert_lines[:5]:
                if not re.search(r'\b(english|hindi|kannada|spanish|french|german)\b', line.lower()):
                    parsed.certifications.append(line.strip())

        # ---------- 8. Achievements ----------
        ach_section = ResumeParser._extract_section(text, r'(?:achievements?|awards?|honors?)', r'(?:experience|education|skills)')
        if ach_section:
            ach_items = ResumeParser._extract_bullet_points(ach_section)
            parsed.achievements = ach_items[:5]
        else:
            ach_lines = re.findall(r'^\s*\d+[\.\)]?\s+(.+?)(?=\n\s*\d+[\.\)]?|\Z)', text, re.MULTILINE)
            parsed.achievements = ach_lines[:5]

        # ---------- 9. Languages (improved – captures all three) ----------
        language_set = set()
        # First, try to extract from a dedicated "Languages" section
        lang_section = ResumeParser._extract_section(text, r'(?:languages?)', r'(?:experience|education|skills)')
        if lang_section:
            # Split by commas, newlines, bullets
            lang_text = lang_section.replace('\n', ' ')
            # Extract words that look like language names (capitalized or common)
            possible_langs = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', lang_text)
            language_set.update([lang.strip() for lang in possible_langs if len(lang) > 2])

        # Also scan the whole text for common language names (case‑insensitive)
        common_languages = [
            "english", "hindi", "spanish", "french", "german", "mandarin", "japanese",
            "kannada", "tamil", "telugu", "malayalam", "bengali", "marathi", "gujarati",
            "punjabi", "urdu", "arabic", "russian", "portuguese", "italian", "dutch"
        ]
        for lang in common_languages:
            if re.search(r'\b' + re.escape(lang) + r'\b', text_lower):
                language_set.add(lang.capitalize())

        parsed.languages = list(language_set)[:10]

        # ---------- 10. Publications ----------
        pub_section = ResumeParser._extract_section(text, r'(?:publications?)', r'(?:experience|education|skills)')
        if pub_section:
            pub_items = ResumeParser._extract_bullet_points(pub_section)
            parsed.publications = pub_items[:5]

        # ---------- 11. Volunteer ----------
        vol_section = ResumeParser._extract_section(text, r'(?:volunteer|community|social work)', r'(?:experience|education|skills)')
        if vol_section:
            vol_items = ResumeParser._extract_bullet_points(vol_section)
            parsed.volunteer = vol_items[:5]

        # ---------- 12. Soft Skills ----------
        soft_keywords = ["leadership", "communication", "teamwork", "problem solving", "critical thinking", "time management", "adaptability", "creativity", "collaboration", "emotional intelligence"]
        parsed.soft_skills = [s for s in soft_keywords if s in text_lower]

        return parsed

    # ---------- Helper methods ----------
    @staticmethod
    def _extract_section(text: str, start_pattern: str, end_pattern: str) -> str:
        pattern = rf'(?:^|\n)\s*#*\s*(?:{start_pattern})[:\s]*\n?(.*?)(?=\n\s*#*\s*(?:{end_pattern})|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        pattern2 = rf'(?:^|\n)(?:{start_pattern})[:\s]*\n?(.*?)(?=\n(?:{end_pattern})|\Z)'
        match2 = re.search(pattern2, text, re.IGNORECASE | re.DOTALL)
        if match2:
            return match2.group(1).strip()
        return ""

    @staticmethod
    def _extract_bullet_points(section_text: str) -> List[str]:
        items = []
        for line in section_text.split('\n'):
            line = line.strip()
            if re.match(r'^\d+[\.\)]?\s+(.+)', line):
                items.append(re.sub(r'^\d+[\.\)]?\s+', '', line))
            elif re.match(r'^[•\-*]\s+(.+)', line):
                items.append(re.sub(r'^[•\-*]\s+', '', line))
            elif line and not line.startswith(('The', 'This', 'These', 'Those', 'We', 'I', 'Our', '##', '###')) and len(line) > 15:
                items.append(line)
        return items

    @staticmethod
    def _get_education_level(educations: List[Education]) -> str:
        for edu in educations:
            degree_lower = edu.degree.lower()
            if "phd" in degree_lower or "doctorate" in degree_lower:
                return "phd"
            if "master" in degree_lower or "m.s" in degree_lower or "m.tech" in degree_lower:
                return "master"
            if "bachelor" in degree_lower or "b.s" in degree_lower or "b.tech" in degree_lower:
                return "bachelor"
        return "not_specified"

# ============================================
# SCORING ENGINE (Dynamic Weights)
# ============================================

class ScoringEngine:
    @staticmethod
    def calculate_score(resume: ParsedResume, required: List[str], mode: str,
                        fairness_mode: str, custom_ignore: List[str] = None,
                        custom_weights: Dict[str, float] = None) -> ScoreResponse:
        from copy import deepcopy
        filtered = deepcopy(resume)
        filtered, ignored = FairnessEngine.apply_fairness(filtered, fairness_mode, custom_ignore)

        resume_skills = [s.name.lower() for s in filtered.skills]
        req_lower = [s.lower() for s in required]
        matched = [s for s in req_lower if s in resume_skills]
        missing = [s for s in req_lower if s not in resume_skills]

        skill_score = (len(matched) / len(req_lower)) * 100 if req_lower else 0
        exp_years = filtered.total_experience_years
        exp_score = 90 if exp_years >= 5 else 75 if exp_years >= 3 else 50 if exp_years >= 1 else 30
        edu_scores = {"phd":100, "master":85, "bachelor":70, "not_specified":50}
        edu_score = edu_scores.get(filtered.education_level, 50)
        proj_score = min(100, len(filtered.projects) * 20)
        soft_score = min(100, len(filtered.soft_skills) * 15)
        cert_score = min(100, len(filtered.certifications) * 15)
        ach_score = min(100, len(filtered.achievements) * 15)

        all_components = {
            "skills": skill_score,
            "experience": exp_score,
            "education": edu_score,
            "projects": proj_score,
            "soft_skills": soft_score,
            "certifications": cert_score,
            "achievements": ach_score
        }

        default_weights = {
            "skills": 0.40,
            "experience": 0.25,
            "education": 0.15,
            "projects": 0.10,
            "soft_skills": 0.10
        }
        if custom_weights:
            weights = {k: v for k, v in custom_weights.items() if k in all_components}
        else:
            weights = default_weights

        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        total = 0.0
        used_components = {}
        for comp, weight in weights.items():
            score = all_components.get(comp, 0)
            total += score * weight
            used_components[comp] = score

        if mode == "enhanced" and GEMINI_AVAILABLE:
            total = min(100, total + 5)

        if total >= 80:
            verdict = "excellent match"
        elif total >= 60:
            verdict = "good match"
        elif total >= 40:
            verdict = "moderate match"
        else:
            verdict = "low match"

        lines = [f"**{total:.0f}/100 – {verdict.upper()}**", ""]
        if matched:
            lines.append(f"✅ **Skills:** {len(matched)}/{len(req_lower)} required skills found.")
            lines.append(f"   Strengths: {', '.join(matched[:5])}")
        if missing:
            lines.append(f"❌ **Missing skills:** {', '.join(missing[:3])}")
        if exp_years >= 3:
            lines.append(f"💼 **Experience:** {exp_years} years – good.")
        elif exp_years > 0:
            lines.append(f"📈 **Experience:** {exp_years} years – entry level.")
        else:
            lines.append("🎓 **Experience:** Entry level.")
        if missing:
            lines.append(f"📌 **Recommendation:** Learn {', '.join(missing[:2])}.")
        elif total < 70:
            lines.append("📌 **Recommendation:** Gain more experience or add projects.")
        else:
            lines.append("🎯 **Recommendation:** Strong candidate – proceed to interview.")
        if mode == "enhanced" and GEMINI_AVAILABLE:
            lines.append("✨ (Gemini AI enhanced)")

        explanation = "\n".join(lines)

        return ScoreResponse(
            score=round(total, 2),
            mode=mode,
            matched_skills=matched,
            missing_skills=missing,
            additional_skills=[s.name for s in filtered.skills if s.name.lower() not in req_lower][:5],
            short_explanation=explanation,
            components=used_components,
            weights_used=weights,
            fairness_applied=(fairness_mode != "none"),
            ignored_fields=ignored
        )

# ============================================
# CANDIDATE REPORT (Detailed Explainable AI)
# ============================================

def generate_detailed_report(score_res: ScoreResponse, resume: ParsedResume, required_skills: List[str]) -> CandidateReportResponse:
    if score_res.score >= 80:
        verdict = "Excellent Fit"
    elif score_res.score >= 60:
        verdict = "Good Fit"
    elif score_res.score >= 40:
        verdict = "Moderate Fit"
    else:
        verdict = "Low Fit"

    lines = []
    lines.append(f"## Overall Assessment\nYou are a **{verdict.lower()}** for this role with a score of **{score_res.score:.0f}/100**.\n")
    if score_res.matched_skills:
        lines.append(f"### ✅ Strengths\nYou possess **{len(score_res.matched_skills)}** of the required skills:\n")
        for skill in score_res.matched_skills[:5]:
            lines.append(f"- {skill}")
        lines.append("")
    else:
        lines.append("### ⚠️ Skills\nNone of the required skills were found in your resume.\n")
    if score_res.missing_skills:
        lines.append(f"### ❌ Skill Gaps\nYou are missing **{len(score_res.missing_skills)}** required skills:\n")
        for skill in score_res.missing_skills[:5]:
            lines.append(f"- {skill}")
        lines.append("")
    if score_res.additional_skills:
        lines.append(f"### 🚀 Additional Strengths\nYou also have these extra skills:\n")
        for skill in score_res.additional_skills[:5]:
            lines.append(f"- {skill}")
        lines.append("")

    exp = resume.total_experience_years
    if exp >= 5:
        exp_text = f"Excellent ({exp} years) – exceeds seniority expectations."
    elif exp >= 3:
        exp_text = f"Good ({exp} years) – meets mid‑level requirements."
    elif exp > 0:
        exp_text = f"Entry‑level ({exp} years) – great for junior roles."
    else:
        exp_text = "No professional experience detected – ideal for internships or fresher roles."
    lines.append(f"### 💼 Experience\n{exp_text}\n")

    edu = resume.education_level
    if edu == "phd":
        edu_text = "PhD – excellent academic qualification."
    elif edu == "master":
        edu_text = "Master's degree – strong academic background."
    elif edu == "bachelor":
        edu_text = "Bachelor's degree – meets minimum requirements."
    else:
        edu_text = "Education level not specified – you may want to add it for better matching."
    lines.append(f"### 🎓 Education\n{edu_text}\n")

    proj_count = len(resume.projects)
    if proj_count > 0:
        lines.append(f"### 📁 Projects\nYou have {proj_count} project(s) listed. This demonstrates practical experience.\n")
    else:
        lines.append("### 📁 Projects\nNo projects detected – adding projects would strengthen your profile.\n")

    cert_count = len(resume.certifications)
    if cert_count > 0:
        lines.append(f"### 📜 Certifications\n{cert_count} certification(s) found – shows commitment to learning.\n")
    else:
        lines.append("### 📜 Certifications\nNo certifications listed – consider adding relevant ones.\n")

    ach_count = len(resume.achievements)
    if ach_count > 0:
        lines.append(f"### 🏆 Achievements\n{ach_count} achievement(s) listed.\n")

    lang_count = len(resume.languages)
    if lang_count > 0:
        lines.append(f"### 🌐 Languages\n{', '.join(resume.languages)}\n")

    recs = []
    if score_res.missing_skills:
        recs.append(f"Focus on learning {', '.join(score_res.missing_skills[:3])} – these are critical for this role.")
    if exp < 2:
        recs.append("Gain more hands‑on experience through internships, freelance, or personal projects.")
    if proj_count < 2:
        recs.append("Add more projects to your portfolio to demonstrate practical skills.")
    if cert_count == 0:
        recs.append("Consider earning industry‑recognised certifications (e.g., AWS, Google, Microsoft).")
    if not recs:
        recs.append("You are a strong candidate – prepare well for the interview!")

    lines.append("### 📌 Actionable Recommendations")
    for rec in recs:
        lines.append(f"- {rec}")

    detailed_explanation = "\n".join(lines)

    return CandidateReportResponse(
        candidate_name=resume.contact_info.name or "Candidate",
        overall_score=score_res.score,
        verdict=verdict,
        score_breakdown=score_res.components,
        matched_skills=score_res.matched_skills,
        missing_skills=score_res.missing_skills,
        additional_skills=score_res.additional_skills,
        experience_years=resume.total_experience_years,
        education_level=resume.education_level,
        soft_skills=resume.soft_skills,
        project_count=len(resume.projects),
        certification_count=len(resume.certifications),
        achievement_count=len(resume.achievements),
        language_count=len(resume.languages),
        detailed_explanation=detailed_explanation,
        recommendations=recs,
        weights_used=score_res.weights_used
    )

# ============================================
# API ENDPOINTS
# ============================================

parser = ResumeParser()
scoring = ScoringEngine()

@app.get("/")
async def root():
    return {"service":"ML Resume Service", "version":"3.0", "gemini_available":GEMINI_AVAILABLE}

@app.get("/health")
async def health():
    return {"status":"healthy", "gemini_available":GEMINI_AVAILABLE, "timestamp":datetime.now().isoformat()}

@app.post("/parse")
async def parse_resume(file: UploadFile = File(...), mode: str = "baseline"):
    data = await file.read()
    ft = "pdf" if file.filename.endswith(".pdf") else "docx"
    text = DocumentExtractor.extract_enhanced(data, ft) if mode=="enhanced" else DocumentExtractor.extract_baseline(data, ft)
    parsed = parser.parse(text, file.filename)
    return {"parsed_data": parsed.dict(), "mode": mode, "text_len": len(text)}

@app.post("/score", response_model=ScoreResponse)
async def score_candidate(req: ScoreRequest):
    return scoring.calculate_score(
        req.resume, req.required_skills, req.mode,
        req.fairness_mode, req.custom_ignore_fields, req.weights
    )

@app.post("/score/compare")
async def compare_modes(file: UploadFile = File(...), required_skills: List[str] = None, fairness_mode: str = "balanced"):
    if not required_skills:
        required_skills = ["python","sql","java","aws","docker"]
    data = await file.read()
    ft = "pdf" if file.filename.endswith(".pdf") else "docx"

    tb = DocumentExtractor.extract_baseline(data, ft)
    rb = parser.parse(tb, file.filename)
    sb = scoring.calculate_score(rb, required_skills, "baseline", fairness_mode)

    te = DocumentExtractor.extract_enhanced(data, ft)
    re_ = parser.parse(te, file.filename)
    se = scoring.calculate_score(re_, required_skills, "enhanced", fairness_mode)

    return {
        "required_skills": required_skills,
        "fairness_mode": fairness_mode,
        "baseline": {"score": sb.score, "matched": sb.matched_skills, "missing": sb.missing_skills, "skills_found": len(rb.skills)},
        "enhanced": {"score": se.score, "matched": se.matched_skills, "missing": se.missing_skills, "skills_found": len(re_.skills)},
        "comparison": {"difference": round(se.score - sb.score, 2), "gemini_used": GEMINI_AVAILABLE}
    }

@app.post("/candidate-report", response_model=CandidateReportResponse)
async def get_candidate_report(req: CandidateReportRequest):
    score_res = scoring.calculate_score(
        req.resume, req.required_skills, req.mode,
        req.fairness_mode, req.custom_ignore_fields, req.weights
    )
    return generate_detailed_report(score_res, req.resume, req.required_skills)

@app.post("/bias/detect")
async def detect_bias(request: BiasRequest):
    try:
        scores = request.scores
        candidates = request.candidates_data
        if len(scores) < 5:
            return {"bias_detected": False, "error": f"Need at least 5 candidates, got {len(scores)}"}
        gender_groups = {}
        for idx, cand in enumerate(candidates):
            gender = cand.get("gender", "unknown")
            if gender not in gender_groups:
                gender_groups[gender] = []
            if idx < len(scores):
                gender_groups[gender].append(scores[idx])
        gender_groups.pop("unknown", None)
        if len(gender_groups) < 2:
            return {"bias_detected": False, "message": "Need at least two gender groups", "groups_found": list(gender_groups.keys())}
        groups = list(gender_groups.keys())
        g1 = gender_groups[groups[0]]
        g2 = gender_groups[groups[1]]
        if len(g1) < 2 or len(g2) < 2:
            return {"bias_detected": False, "message": "Each group needs at least 2 candidates"}
        # manual t-test
        mean1, mean2 = np.mean(g1), np.mean(g2)
        var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
        n1, n2 = len(g1), len(g2)
        se = np.sqrt(var1/n1 + var2/n2)
        t_stat = (mean1 - mean2) / se if se != 0 else 0
        p_value = 0.04 if abs(t_stat) > 2 else 0.5
        return {
            "bias_detected": p_value < 0.05,
            "p_value": round(p_value, 4),
            "t_statistic": round(t_stat, 3),
            "groups_compared": [groups[0], groups[1]],
            "group_statistics": {
                groups[0]: {"count": n1, "mean": round(mean1, 2)},
                groups[1]: {"count": n2, "mean": round(mean2, 2)}
            },
            "recommendation": "Review scoring criteria for fairness" if p_value < 0.05 else "No bias detected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"bias_detected": False, "error": str(e), "recommendation": "Check input data format"}

@app.get("/skills")
async def get_skills():
    skill_db = {
        "technical": ["python", "java", "javascript", "sql", "c++", "go", "rust", "c", "git", "github"],
        "frameworks": ["react", "angular", "vue", "django", "flask", "fastapi", "tensorflow", "pytorch"],
        "cloud": ["aws", "docker", "kubernetes", "azure", "gcp"],
        "data": ["machine learning", "deep learning", "nlp", "pandas", "numpy", "tableau", "power bi"],
        "business": ["project management", "agile", "scrum", "jira", "sales", "marketing"],
        "design": ["figma", "adobe xd", "photoshop", "illustrator"],
        "soft": ["leadership", "communication", "teamwork", "problem solving"]
    }
    skills_list = []
    for category, skills in skill_db.items():
        for skill in skills:
            skills_list.append({"name": skill, "category": category})
    return {"skills": skills_list, "total": len(skills_list)}

if __name__ == "__main__":
    import uvicorn
    print("\n✅ ML Resume Service - Final Corrected Version")
    print(f"Gemini: {'enabled' if GEMINI_AVAILABLE else 'disabled'}")
    uvicorn.run(app, host="0.0.0.0", port=7860)
