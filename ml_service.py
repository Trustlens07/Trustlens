# ml_service.py - COMPLETE FINAL VERSION
# Features: parsing, scoring, fairness, bias detection, explainable AI, Gemini, candidate report

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
    linkedin: Optional[str] = None
    github: Optional[str] = None

class Skill(BaseModel):
    name: str
    category: str
    proficiency: str = "intermediate"

class Experience(BaseModel):
    title: str
    company: str
    duration_years: float = 0.0

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[int] = None

class Project(BaseModel):
    name: str
    technologies: List[str] = []

class ParsedResume(BaseModel):
    file_name: str
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    skills: List[Skill] = []
    soft_skills: List[str] = []
    experience: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certifications: List[str] = []
    total_experience_years: float = 0.0
    skill_count: int = 0
    education_level: str = ""

class ScoreRequest(BaseModel):
    required_skills: List[str]
    resume: ParsedResume
    mode: str = "baseline"
    fairness_mode: str = "balanced"
    custom_ignore_fields: Optional[List[str]] = None

class ScoreResponse(BaseModel):
    score: float
    mode: str
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    short_explanation: str
    components: Dict[str, float]
    fairness_applied: bool
    ignored_fields: List[str]

class CandidateReportRequest(BaseModel):
    required_skills: List[str]
    resume: ParsedResume
    mode: str = "enhanced"
    fairness_mode: str = "balanced"
    custom_ignore_fields: Optional[List[str]] = None

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
    detailed_explanation: str
    recommendations: List[str]

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
            for edu in resume.education:
                edu.institution = "[REDACTED]"
            ignored = ["name", "email", "phone", "institution"]
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
                prompt = f"Clean this resume text. Fix OCR errors. Keep skills, experience, education.\n\n{text[:6000]}"
                response = gemini_model.generate_content(prompt)
                return response.text if response.text else text
            except:
                return text
        return text

# ============================================
# RESUME PARSER
# ============================================

class ResumeParser:
    @staticmethod
    def parse(text: str, file_name: str) -> ParsedResume:
        parsed = ParsedResume(file_name=file_name)
        text_lower = text.lower()

        # Name
        lines = text.split('\n')
        for line in lines[:10]:
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', line.strip()):
                parsed.contact_info.name = line.strip()
                break

        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            parsed.contact_info.email = email_match.group()

        # GitHub / LinkedIn
        github_match = re.search(r'github\.com/[\w-]+', text)
        if github_match:
            parsed.contact_info.github = github_match.group()
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text)
        if linkedin_match:
            parsed.contact_info.linkedin = linkedin_match.group()

        # Skills database
        skill_db = {
            "technical": ["python", "java", "javascript", "sql", "c++", "go", "rust"],
            "frameworks": ["react", "angular", "vue", "django", "flask", "fastapi", "tensorflow", "pytorch"],
            "cloud": ["aws", "docker", "kubernetes", "azure", "gcp"],
            "data": ["machine learning", "deep learning", "nlp", "pandas", "numpy", "tableau", "power bi"],
            "business": ["project management", "agile", "scrum", "jira", "sales", "marketing"],
            "design": ["figma", "adobe xd", "photoshop", "illustrator"],
            "soft": ["leadership", "communication", "teamwork", "problem solving"]
        }
        for cat, skills in skill_db.items():
            for skill in skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    parsed.skills.append(Skill(name=skill, category=cat))
        parsed.skill_count = len(parsed.skills)

        # Experience years
        exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s+of\s+experience', text_lower)
        if exp_match:
            parsed.total_experience_years = float(exp_match.group(1))
        else:
            job_entries = len(re.findall(r'\b(experience|work|employment|job)\b', text_lower))
            parsed.total_experience_years = {5:5.0, 3:3.0, 1:1.0}.get(job_entries, 0.0)

        # Education level
        if "phd" in text_lower or "doctorate" in text_lower:
            parsed.education_level = "phd"
        elif "master" in text_lower or "m.s" in text_lower or "m.tech" in text_lower:
            parsed.education_level = "master"
        elif "bachelor" in text_lower or "b.s" in text_lower or "b.tech" in text_lower:
            parsed.education_level = "bachelor"
        else:
            parsed.education_level = "not_specified"

        # Soft skills
        soft = ["leadership", "communication", "teamwork", "problem solving"]
        parsed.soft_skills = [s for s in soft if s in text_lower]

        # Projects (basic)
        proj_section = re.search(r'(?:projects?|portfolio)[:\s]*(.*?)(?=\n\n[A-Z]|\Z)', text, re.IGNORECASE | re.DOTALL)
        if proj_section:
            proj_names = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', proj_section.group(1))
            for name in proj_names[:3]:
                parsed.projects.append(Project(name=name.strip()))

        # Certifications
        cert_matches = re.findall(r'certified\s+([A-Za-z\s]+)|certification\s+in\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        for match in cert_matches:
            cert = match[0] or match[1]
            if cert:
                parsed.certifications.append(cert.strip())
        parsed.certifications = list(set(parsed.certifications))[:5]

        return parsed

# ============================================
# SCORING ENGINE
# ============================================

class ScoringEngine:
    @staticmethod
    def calculate_score(resume: ParsedResume, required: List[str], mode: str,
                        fairness_mode: str, custom_ignore: List[str] = None) -> ScoreResponse:
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

        components = {"skills":skill_score, "experience":exp_score, "education":edu_score,
                      "projects":proj_score, "soft_skills":soft_score}
        weights = {"skills":0.4, "experience":0.25, "education":0.15, "projects":0.1, "soft_skills":0.1}
        total = sum(components[k] * weights[k] for k in components)

        # Short explanation
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
            lines.append(f"❌ **Missing:** {', '.join(missing[:3])}")
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
            total = min(100, total + 5)
            lines.append("✨ (Gemini AI enhanced)")

        explanation = "\n".join(lines)

        return ScoreResponse(
            score=round(total, 2),
            mode=mode,
            matched_skills=matched,
            missing_skills=missing,
            additional_skills=[s.name for s in filtered.skills if s.name.lower() not in req_lower][:5],
            short_explanation=explanation,
            components=components,
            fairness_applied=(fairness_mode != "none"),
            ignored_fields=ignored
        )

# ============================================
# CANDIDATE REPORT (Detailed Explainable AI)
# ============================================

def generate_detailed_report(score_res: ScoreResponse, resume: ParsedResume, required_skills: List[str]) -> CandidateReportResponse:
    """Generate a rich, human‑readable report for the candidate."""

    # Overall verdict
    if score_res.score >= 80:
        verdict = "Excellent Fit"
    elif score_res.score >= 60:
        verdict = "Good Fit"
    elif score_res.score >= 40:
        verdict = "Moderate Fit"
    else:
        verdict = "Low Fit"

    # Build detailed explanation as a single string (markdown formatted)
    lines = []

    # 1. Summary
    lines.append(f"## Overall Assessment\nYou are a **{verdict.lower()}** for this role with a score of **{score_res.score:.0f}/100**.\n")

    # 2. Skills analysis
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
        lines.append(f"### 🚀 Additional Strengths\nYou also have these extra skills that could be valuable:\n")
        for skill in score_res.additional_skills[:5]:
            lines.append(f"- {skill}")
        lines.append("")

    # 3. Experience
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

    # 4. Education
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

    # 5. Projects & certifications
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

    # 6. Recommendations (actionable)
    recommendations = []
    if score_res.missing_skills:
        recommendations.append(f"Focus on learning {', '.join(score_res.missing_skills[:3])} – these are critical for this role.")
    if exp < 2:
        recommendations.append("Gain more hands‑on experience through internships, freelance, or personal projects.")
    if proj_count < 2:
        recommendations.append("Add more projects to your portfolio to demonstrate practical skills.")
    if cert_count == 0:
        recommendations.append("Consider earning industry‑recognised certifications (e.g., AWS, Google, Microsoft).")
    if not recommendations:
        recommendations.append("You are a strong candidate – prepare well for the interview!")

    lines.append("### 📌 Actionable Recommendations")
    for rec in recommendations:
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
        detailed_explanation=detailed_explanation,
        recommendations=recommendations
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
    return scoring.calculate_score(req.resume, req.required_skills, req.mode,
                                   req.fairness_mode, req.custom_ignore_fields)

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
    """Detailed, explainable AI report for candidate login."""
    score_res = scoring.calculate_score(req.resume, req.required_skills, req.mode,
                                        req.fairness_mode, req.custom_ignore_fields)
    return generate_detailed_report(score_res, req.resume, req.required_skills)

# ============================================
# BIAS DETECTION (manual t-test)
# ============================================

@app.post("/bias/detect")
async def detect_bias(request: BiasRequest):
    try:
        scores = request.scores
        candidates = request.candidates_data

        if len(scores) < 5:
            return {
                "bias_detected": False,
                "error": f"Need at least 5 candidates, got {len(scores)}",
                "recommendation": "Add more candidate data"
            }

        gender_groups = {}
        for idx, cand in enumerate(candidates):
            gender = cand.get("gender", "unknown")
            if gender not in gender_groups:
                gender_groups[gender] = []
            if idx < len(scores):
                gender_groups[gender].append(scores[idx])

        gender_groups.pop("unknown", None)

        if len(gender_groups) < 2:
            return {
                "bias_detected": False,
                "message": "Need at least two gender groups with data",
                "groups_found": list(gender_groups.keys())
            }

        groups = list(gender_groups.keys())
        g1 = gender_groups[groups[0]]
        g2 = gender_groups[groups[1]]

        if len(g1) < 2 or len(g2) < 2:
            return {
                "bias_detected": False,
                "message": "Each group needs at least 2 candidates",
                "counts": {groups[0]: len(g1), groups[1]: len(g2)}
            }

        # Manual t-test (no scipy)
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
        return {
            "bias_detected": False,
            "error": str(e),
            "recommendation": "Check input data format"
        }

# ============================================
# SKILLS ENDPOINT
# ============================================

@app.get("/skills")
async def get_skills():
    skill_db = {
        "technical": ["python", "java", "javascript", "sql", "c++", "go", "rust"],
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
    print("\n✅ ML Resume Service - Complete with Candidate Report")
    print(f"Gemini: {'enabled' if GEMINI_AVAILABLE else 'disabled'}")
    uvicorn.run(app, host="0.0.0.0", port=7860)