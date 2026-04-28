# TrustLens – Fairness AI Recruitment Platform

> AI-Powered Resume Screening with Bias Detection, Fairness Monitoring & Explainable Decisions

TrustLens is an end-to-end AI recruitment platform that detects, measures, and mitigates unconscious bias in AI-powered hiring systems. It combines intelligent resume parsing, explainable AI scoring, statistical fairness analysis, blind screening, and complete audit logging — delivered through a scalable microservice architecture using React, FastAPI, PostgreSQL, Redis, Hugging Face, and Google Cloud.

---

# 🌍 Why TrustLens Matters

Modern AI hiring systems often inherit historical and demographic bias from training data. This can result in unfair screening decisions across gender, ethnicity, location, and educational background.

TrustLens helps organizations:

- Detect bias in recruitment pipelines
- Monitor fairness metrics continuously
- Apply active debiasing techniques
- Explain AI-generated hiring decisions
- Maintain audit-ready compliance records
- Build transparent and ethical hiring workflows

---

# 🎯 Problem & Solution

| Problem | TrustLens Solution |
|---|---|
| Gender and ethnicity bias in AI scoring | Demographic parity adjustment, disparate impact monitoring, equal opportunity analysis |
| Name/location discrimination | Blind resume screening with configurable redaction |
| Opaque AI decisions | Explainable reports with strengths, weaknesses, and AI reasoning |
| Lack of fairness monitoring | Statistical fairness metrics with recommendations |
| Compliance and audit risks | Complete audit logging for all screening actions |
| Scanned or image resumes | OCR fallback using OCR.space and Tesseract |

---

# ✨ Key Features

- 📄 AI-powered resume parsing
- 🧠 Explainable AI candidate scoring
- ⚖️ Bias detection and fairness analysis
- 🕶️ Blind screening support
- 📊 Statistical fairness metrics
- 🧾 Complete audit logging
- ☁️ Cloud-native deployment
- 🔍 OCR support for scanned resumes
- 📈 Candidate ranking and comparison
- 🤖 Gemini-powered enhancement APIs

---

# 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Clients                                       │
│                    (Web App, Mobile, ATS Integrations)                     │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ HTTP/JSON
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                     React Frontend (Vite + Tailwind)                       │
│                                                                             │
│  Upload • Dashboard • Analytics • Firebase Authentication                  │
│                                                                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ HTTPS / JSON
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                  FastAPI Backend (Google Cloud Run)                        │
│                                                                             │
│  Auth • API Router • Middleware • Audit Logging • Rate Limiting            │
│                                                                             │
│  Screening Orchestrator • Bias Analysis • Upload Pipeline                  │
│                                                                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ Internal API Calls
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                ML Service (Hugging Face Spaces)                            │
│                                                                             │
│  Resume Parsing • AI Scoring • Bias Detection • Gemini APIs                │
│                                                                             │
│  Sentence-BERT • Gemini • OCR.space • Tesseract                            │
│                                                                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                              Data Layer                                    │
│                                                                             │
│  PostgreSQL • Redis • Supabase Storage                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---
# 🛠️ Tech Stack

## Frontend
- React
- Vite
- Tailwind CSS
- React Query
- Zustand
- Firebase Authentication

## Backend
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis

## ML & AI
- Sentence-BERT
- Google Gemini API
- Hugging Face Spaces
- OCR.space
- Tesseract OCR

## Cloud & DevOps
- Docker
- Google Cloud Run
- Supabase
- GitHub Actions

---

# ⚖️ Fairness Metrics & Debiasing

## Demographic Parity Ratio

```text
ratio = min(group_mean_scores) / max(group_mean_scores)
```

Threshold:
- 0.8 (80% Rule — EEOC Standard)

---

## Equal Opportunity Difference

```text
diff = max(TPR_groups) - min(TPR_groups)
```

Where:
- TPR = True Positive Rate

---

## Disparate Impact

```text
impact = group_selection_rate / max_selection_rate
```

---

## Active Debiasing Methods

### Demographic Parity Adjustment
Algorithmic score reweighting to reduce unfair demographic advantages.

### Blind Resume Processing
Configurable redaction levels:
- Strict
- Balanced
- Maximum

### Fairness Recommendation Engine
Provides mitigation strategies when unfair outcomes are detected.

---

# 📊 Explainable AI Reports

TrustLens generates human-readable reports containing:

- Candidate strengths
- Missing skills
- Experience quality analysis
- Career stability indicators
- AI-generated interview questions
- Score explanations
- Improvement recommendations

---

# 🚀 Quick Start (Local Development)

# Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional)
- Tesseract OCR (optional)

---

# Backend Setup

```bash
cd TrustLens/backend

python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env

alembic upgrade head

python -m uvicorn app.main:app --reload --port 8000
```

---

# Frontend Setup

```bash
cd trustlens-frontend

npm install

cp .env.example .env

npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

# ML Service Setup

```bash
cd ml-service-api

python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

export GEMINI_API_KEY="your_key"

python ml_service.py
```

ML service runs at:

```text
http://localhost:7860
```

---

# 🔌 Environment Variables

## Frontend

```env
VITE_API_BASE_URL=https://resume-backend-948277799081.us-central1.run.app
```

---

## ML Service

```env
GEMINI_API_KEY=your_google_ai_key
```

---

# 📡 Backend API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/health` | Health check | No |
| GET | `/ready` | Readiness check | No |
| POST | `/api/v1/upload` | Upload resume | Yes |
| GET | `/api/v1/candidates` | List candidates | Yes |
| POST | `/api/v1/candidates` | Create candidate | Yes |
| POST | `/api/v1/screening` | Batch screening | Yes |
| POST | `/api/v1/bias/analyze` | Fairness analysis | Yes |
| POST | `/api/v1/candidates/{id}/enhance` | Enhanced scoring | Yes |

---

# 🤖 ML Service Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/parse` | Extract structured resume data |
| POST | `/score` | Baseline or enhanced scoring |
| POST | `/score/compare` | Compare baseline vs enhanced |
| POST | `/candidate-report` | Human-readable candidate report |
| POST | `/bias/detect` | Statistical fairness analysis |
| POST | `/gemini/explain-score` | Explain score differences |
| POST | `/gemini/interview-questions` | Generate interview questions |
| POST | `/gemini/extract-skills` | Extract skills from JD |
| POST | `/gemini/rank-candidates` | Rank candidates |

---

# 🧪 Testing

## Backend Tests

```bash
pytest

pytest app/tests/test_api/test_bias.py -v

pytest --cov=app --cov-report=html
```

---

## Frontend Tests

```bash
npm run test
```

---

# ☁️ Deployment

# Docker (Backend)

```bash
docker build -t trustlens-backend .

docker run -p 8080:8080 \
  -e DATABASE_URL=... \
  -e FIREBASE_KEY='{...}' \
  trustlens-backend
```

---

# Google Cloud Run

```bash
gcloud run deploy trustlens-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=...,FIREBASE_KEY=secret"
```

---

# Frontend Production Build

```bash
cd trustlens-frontend

npm run build
```

Deploy:
- Firebase Hosting
- Vercel
- Netlify
- Cloud Run + Nginx

---

# Hugging Face Spaces

ML service deployed at:

```text
https://preeee-276-ml-service-api.hf.space
```

---

# 📂 Project Structure

```text
TrustLens/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── middlewares/
│   │   ├── orchestrators/
│   │   ├── services/
│   │   └── tests/
│   ├── migrations/
│   └── Dockerfile
│
├── trustlens-frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── vite.config.ts
│
└── ml-service-api/
    ├── ml_service.py
    ├── requirements.txt
    └── Dockerfile
```

---

# 🔒 Security & Compliance

- JWT Authentication (Firebase)
- Role-protected API endpoints
- TrustedHostMiddleware
- CORS origin whitelist
- SQL injection prevention
- File type validation
- Audit logging
- Rate limiting
- Secure cloud deployment

---

# 📈 Example Fairness Analysis Output

```json
{
  "demographic_parity_ratio": 0.84,
  "equal_opportunity_difference": 0.07,
  "disparate_impact": 0.81,
  "bias_detected": false,
  "recommendation": "No major fairness concerns detected."
}
```

---

# 🌍 UN Sustainable Development Goals

TrustLens aligns with:

- SDG 8 — Decent Work and Economic Growth
- SDG 10 — Reduced Inequalities
- SDG 16 — Peace, Justice and Strong Institutions

---

# 🚧 Future Enhancements

- Real-time fairness drift monitoring
- SHAP-based explainability
- Multi-language resume support
- Interview transcript analysis
- LLM hallucination detection
- Enterprise ATS integrations
- Fairness benchmarking dashboard

---

# 📸 Screenshots

## Dashboard
_Add screenshot here_

## Bias Analytics
_Add screenshot here_

## Candidate Report
_Add screenshot here_

## Blind Screening
_Add screenshot here_

---

# 🔗 Live Demo & Links

## ML Service API
https://preeee-276-ml-service-api.hf.space/docs

## Backend API
https://resume-backend-948277799081.us-central1.run.app

## Frontend (Development)
http://localhost:5173

---

# 📄 License

MIT License

See `LICENSE` for more information.

---

# 🙏 Acknowledgments

- FastAPI
- SQLAlchemy
- Alembic
- React
- Tailwind CSS
- Hugging Face
- Google Gemini API
- Firebase
- Google Cloud Run
- OCR.space
- Tesseract OCR

---

# ❤️ Built for Fairer Hiring

TrustLens was built to promote ethical, transparent, and inclusive AI-powered recruitment systems.
