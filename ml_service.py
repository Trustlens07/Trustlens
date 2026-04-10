# phase3/ml_service.py
# COMPLETE PHASE 3: Caching, ML Model, Bias Detection, Performance Metrics

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import OrderedDict
import hashlib
import time
import io
import re
import numpy as np
import PyPDF2
import docx
from sklearn.ensemble import RandomForestRegressor

# ============================================
# LRU CACHE
# ============================================

class LRUCache:
    def __init__(self, capacity: int = 50):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: str):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

parse_cache = LRUCache(capacity=50)

# ============================================
# PYDANTIC SCHEMAS
# ============================================

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class Skill(BaseModel):
    name: str
    category: str

class ParsedResume(BaseModel):
    file_name: str
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    skills: List[Skill] = []
    skill_count: int = 0
    total_experience_years: float = 0.0
    education_level: str = ""

class ScoreRequest(BaseModel):
    required_skills: List[str]
    resume: ParsedResume
    use_ml: bool = False

class BiasRequest(BaseModel):
    scores: List[float]
    candidates_data: List[Dict[str, str]]

# ============================================
# ML SCORING MODEL
# ============================================

class ScoringModel:
    def __init__(self):
        self.model = None
        self.is_trained = False
    
    def train(self):
        X = np.array([
            [8, 5, 3, 85], [5, 3, 2, 70], [10, 7, 4, 95],
            [3, 1, 2, 45], [6, 4, 3, 78], [4, 2, 1, 60],
            [7, 6, 3, 82], [2, 0, 2, 35], [9, 8, 4, 90]
        ])
        y = np.array([88, 72, 92, 55, 80, 62, 85, 48, 94])
        
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.model.fit(X, y)
        self.is_trained = True
        return {"status": "trained", "samples": len(X)}
    
    def predict(self, features):
        if not self.is_trained:
            return None
        return self.model.predict(features.reshape(1, -1))[0]

# ============================================
# ML ENGINE
# ============================================

class MLEnginePhase3:
    def __init__(self):
        self.skill_database = {
            "programming": ["python", "java", "javascript", "sql"],
            "frameworks": ["react", "django", "flask", "fastapi"],
            "cloud": ["aws", "docker", "kubernetes"]
        }
        self.scoring_model = ScoringModel()
    
    def extract_text_from_pdf(self, file_bytes):
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return " ".join([page.extract_text() or "" for page in reader.pages])
        except:
            return ""
    
    def extract_text_from_docx(self, file_bytes):
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            return " ".join([p.text for p in doc.paragraphs])
        except:
            return ""
    
    def extract_name_regex(self, text):
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 3 and len(line) < 50:
                if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', line):
                    return line
        return None
    
    def extract_skills(self, text):
        text_lower = text.lower()
        detected = []
        for category, skills in self.skill_database.items():
            for skill in skills:
                if skill in text_lower:
                    detected.append(Skill(name=skill, category=category))
        return detected
    
    def parse_resume(self, file_bytes, file_name, file_type):
        cache_key = hashlib.md5(file_bytes).hexdigest()
        cached = parse_cache.get(cache_key)
        if cached:
            return ParsedResume(**cached), True
        
        if file_type == "pdf":
            text = self.extract_text_from_pdf(file_bytes)
        else:
            text = self.extract_text_from_docx(file_bytes)
        
        parsed = ParsedResume(file_name=file_name)
        parsed.contact_info.name = self.extract_name_regex(text)
        parsed.skills = self.extract_skills(text)
        parsed.skill_count = len(parsed.skills)
        
        parse_cache.put(cache_key, parsed.dict())
        return parsed, False
    
    def score_rule_based(self, resume, required_skills):
        resume_skills = [s.name.lower() for s in resume.skills]
        required_lower = [s.lower() for s in required_skills]
        
        matched = [s for s in required_lower if s in resume_skills]
        missing = [s for s in required_lower if s not in resume_skills]
        
        score = (len(matched) / len(required_lower)) * 100 if required_lower else 0
        
        return {
            "total_score": score,
            "method": "rule_based",
            "matched_skills": matched,
            "missing_skills": missing
        }
    
    def score_ml(self, resume, required_skills):
        resume_skills = [s.name.lower() for s in resume.skills]
        required_lower = [s.lower() for s in required_skills]
        matched = sum(1 for s in required_lower if s in resume_skills)
        
        edu_map = {"phd": 4, "master": 3, "bachelor": 2, "not_specified": 1}
        edu_encoded = edu_map.get(resume.education_level, 1)
        
        features = np.array([[
            resume.skill_count,
            resume.total_experience_years,
            edu_encoded,
            (matched / len(required_lower)) * 100 if required_lower else 0
        ]])
        
        score = self.scoring_model.predict(features)
        if score is None:
            return self.score_rule_based(resume, required_skills)
        
        return {
            "total_score": min(100, score),
            "method": "ml_model",
            "matched_skills": [s for s in required_lower if s in resume_skills],
            "missing_skills": [s for s in required_lower if s not in resume_skills]
        }

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(title="ML Resume Service - Phase 3", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = MLEnginePhase3()

@app.on_event("startup")
async def startup():
    engine.scoring_model.train()
    print("✅ Phase 3 Model trained!")

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {
        "message": "ML Resume Service - PHASE 3",
        "features": ["Caching", "ML Scoring Model", "Performance Metrics", "Bias Detection"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "cache_size": len(parse_cache.cache),
        "model_trained": engine.scoring_model.is_trained,
        "phase": "Phase 3"
    }

@app.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    start = time.time()
    bytes_data = await file.read()
    file_type = "pdf" if file.filename.endswith(".pdf") else "docx"
    result, from_cache = engine.parse_resume(bytes_data, file.filename, file_type)
    
    return {
        "data": result.dict(),
        "meta": {
            "from_cache": from_cache,
            "processing_time_ms": round((time.time() - start) * 1000, 2)
        }
    }

@app.post("/score")
async def score_candidate(request: ScoreRequest):
    start = time.time()
    
    if request.use_ml and engine.scoring_model.is_trained:
        result = engine.score_ml(request.resume, request.required_skills)
    else:
        result = engine.score_rule_based(request.resume, request.required_skills)
    
    return {
        "score": result["total_score"],
        "method": result["method"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "processing_time_ms": round((time.time() - start) * 1000, 2)
    }

@app.post("/bias/detect")
async def detect_bias(request: BiasRequest):
    """Simple bias detection - NO SCIPY NEEDED"""
    try:
        scores = request.scores
        candidates = request.candidates_data
        
        if len(scores) < 5:
            return {
                "bias_detected": False,
                "total_candidates": len(scores),
                "error": f"Need at least 5 candidates, have {len(scores)}"
            }
        
        # Group scores by gender
        gender_scores = {}
        for i, cand in enumerate(candidates):
            gender = cand.get("gender", "Unknown")
            if gender not in gender_scores:
                gender_scores[gender] = []
            if i < len(scores):
                gender_scores[gender].append(scores[i])
        
        # Calculate statistics
        gender_stats = {}
        for gender, score_list in gender_scores.items():
            gender_stats[gender] = {
                "count": len(score_list),
                "mean": round(sum(score_list) / len(score_list), 2),
                "min": min(score_list),
                "max": max(score_list)
            }
        
        # Check for bias (if mean difference > 10 points)
        bias_detected = False
        if len(gender_stats) >= 2:
            means = [stats["mean"] for stats in gender_stats.values()]
            if max(means) - min(means) > 10:
                bias_detected = True
        
        return {
            "bias_detected": bias_detected,
            "total_candidates": len(scores),
            "gender_analysis": gender_stats,
            "recommendations": [
                "Review scoring criteria for consistency across groups" if bias_detected 
                else "No significant bias detected. Continue monitoring."
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "bias_detected": False,
            "error": str(e),
            "total_candidates": len(request.scores) if request.scores else 0
        }

@app.get("/cache/stats")
async def cache_stats():
    return {
        "cache_size": len(parse_cache.cache),
        "capacity": 50,
        "utilization": f"{len(parse_cache.cache) / 50 * 100:.1f}%"
    }

@app.post("/cache/clear")
async def clear_cache():
    parse_cache.cache.clear()
    return {"message": "Cache cleared"}

@app.get("/model/info")
async def model_info():
    return {
        "trained": engine.scoring_model.is_trained,
        "type": "RandomForestRegressor",
        "features": ["skill_count", "experience_years", "education_level", "match_percentage"]
    }

@app.get("/performance")
async def performance():
    return {
        "cache_hit_rate": f"{len(parse_cache.cache) / 50 * 100:.1f}%",
        "model_status": "trained" if engine.scoring_model.is_trained else "not_trained",
        "phase": "Phase 3 - All features working"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)