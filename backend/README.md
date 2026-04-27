# TrustLens Backend

**AI-Powered Resume Screening with Bias Detection & Fairness Monitoring**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 Overview

TrustLens backend provides a comprehensive API for detecting and mitigating bias in AI-powered hiring decisions. It combines resume parsing, intelligent scoring, and advanced fairness analytics to ensure equitable candidate evaluation.

### Key Features

- 🔍 **Resume Parsing** - Extract structured data from PDF, DOC, DOCX files
- 📊 **Intelligent Scoring** - AI-powered candidate evaluation with skill matching
- ⚖️ **Bias Detection** - Statistical fairness metrics (demographic parity, equal opportunity, disparate impact)
- 🛡️ **Active Debiasing** - Algorithmic score adjustments to ensure group fairness
- 👁️ **Blind Screening** - Remove identifying information to reduce unconscious bias
- 📈 **Audit Logging** - Complete compliance tracking for all decisions
- 🤖 **Multi-ML Integration** - Hugging Face + Gemini AI for enhanced analysis
- 🔐 **Firebase Auth** - Secure JWT-based authentication
- ☁️ **Cloud Ready** - Docker + Google Cloud Run deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                             │
│  (Web App, Mobile, ATS Integrations)                       │
└─────────────────────┬─────────────────────────────────────┘
                      │ HTTP/JSON
┌─────────────────────▼─────────────────────────────────────┐
│                    FastAPI App                             │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │   Auth      │ │    API       │ │   Middleware        │  │
│  │ (Firebase)  │ │  (v1 Router) │ │(Audit, CORS, Rate)  │  │
│  └─────────────┘ └──────────────┘ └─────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Business Logic Layer                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │   │
│  │  │ Screening│ │  Upload   │ │ Bias Analysis    │    │   │
│  │  │Orchestrator│ │Orchestrator│ │Orchestrator    │    │   │
│  │  └────┬─────┘ └────┬─────┘ └────────┬─────────┘    │   │
│  │       └─────────────┴──────────────┬──┘              │   │
│  │  ┌─────────────────────────────────▼──────┐         │   │
│  │  │         Service Layer                  │         │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌────────┐ │         │   │
│  │  │  │ MLClient │ │Debiasing │ │Storage │ │         │   │
│  │  │  │ (HF/Gemini)│ │ Service  │ │ Service│ │         │   │
│  │  │  └──────────┘ └──────────┘ └────────┘ │         │   │
│  │  └────────────────────────────────────────┘         │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ PostgreSQL   │  │    Redis     │  │   Supabase      │   │
│  │(Candidates,  │  │   (Cache)    │  │   (Storage)     │   │
│  │  Scores,     │  │              │  │                 │   │
│  │BiasMetrics)  │  │              │  │                 │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or Supabase)
- Redis (optional, for caching)
- Firebase project (for authentication)

### Installation

```bash
# Clone repository
cd Trustlens/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Create `.env` file:

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trustlens

# Supabase (optional, for storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Firebase Authentication
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-credentials.json
# OR for Cloud Run:
FIREBASE_KEY={"type": "service_account", ...}

# ML Services
ML_PARSING_SERVICE_URL=https://your-ml-service.hf.space
ML_SCORING_SERVICE_URL=https://your-ml-service.hf.space
ML_BIAS_SERVICE_URL=https://your-ml-service.hf.space

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,*.localhost
CORS_ORIGINS=http://localhost:3000,http://localhost:3003

# Optional: Redis Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=1800

# Optional: Audit Logging
AUDIT_LOG_ENABLED=true
```

## 📚 API Documentation

### Core Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/ready` | GET | Readiness probe | No |
| `/docs` | GET | Swagger UI | No |
| `/api/v1/auth/test-token` | GET | Verify JWT token | Yes |
| `/api/v1/upload` | POST | Upload resume | Yes |
| `/api/v1/candidates` | GET/POST | List/Create candidates | Yes |
| `/api/v1/screening` | POST | Batch screening | Yes |
| `/api/v1/bias/analyze` | POST | Analyze fairness | Yes |
| `/api/v1/bias/metrics` | GET | Get bias metrics | Yes |
| `/api/v1/candidates/{id}/enhance` | POST | AI-enhanced scoring | Yes |

### Bias Analysis Example

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/bias/analyze \
  -H "Authorization: Bearer <firebase_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {"id": "c1", "score": 85.0, "protected_attributes": {"gender": "female"}},
      {"id": "c2", "score": 82.0, "protected_attributes": {"gender": "female"}},
      {"id": "c3", "score": 78.0, "protected_attributes": {"gender": "male"}},
      {"id": "c4", "score": 80.0, "protected_attributes": {"gender": "male"}}
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "bias_detected": false,
    "demographic_parity_ratio": 0.96,
    "equal_opportunity_diff": 4.5,
    "group_means": {
      "gender_female": 83.5,
      "gender_male": 79.0
    },
    "recommendations": [
      "No significant bias detected. Current scoring appears fair across groups."
    ]
  }
}
```

### Batch Screening Example

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/screening/batch \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_role": "Senior Software Engineer",
    "job_description": "Looking for experienced Python developers...",
    "fairness_mode": "balanced",
    "resumes": [
      {
        "filename": "candidate1.pdf",
        "content": "<base64_encoded_content>",
        "file_type": "pdf"
      }
    ]
  }'
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/test_api/test_bias.py -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run integration tests
pytest app/tests/test_integration/ -v
```

## 🔒 Security Features

- **Firebase JWT Authentication** - Secure token-based auth
- **TrustedHostMiddleware** - Prevents host header attacks
- **CORS Protection** - Configurable origin whitelist
- **Input Validation** - File type/size validation with magic bytes
- **Audit Logging** - Complete request/response logging for compliance
- **SQL Injection Protection** - Parameterized queries via SQLAlchemy
- **XSS Protection** - Input sanitization middleware

## ⚖️ Fairness Metrics

### Demographic Parity
Measures if different groups receive similar average scores.
```
Demographic Parity Ratio = min(group_means) / max(group_means)
Threshold: 0.8 (80% rule)
```

### Equal Opportunity
Measures if qualified candidates have equal selection rates across groups.
```
Equal Opportunity Diff = max(TPR_groups) - min(TPR_groups)
```

### Disparate Impact
Legal standard: groups should have selection rates within 80% of the highest.
```
Disparate Impact = group_selection_rate / max_selection_rate
```

## 🛠️ Development

### Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── core/                 # Config, database, logging
│   ├── middlewares/          # Audit, error handling, rate limiting
│   ├── models/               # SQLAlchemy models
│   ├── orchestrators/        # Business logic coordination
│   ├── services/             # ML clients, debiasing, storage
│   ├── utils/                # Validation, sanitization
│   └── tests/                # Test suites
├── docs/                     # API contracts, documentation
├── migrations/               # Alembic database migrations
├── Dockerfile                # Container build
└── requirements.txt          # Python dependencies
```

### Key Components

#### Bias Detection (`app/services/debiasing.py`)
```python
from app.services.debiasing import BiasMitigator

# Demographic parity adjustment
result = BiasMitigator.demographic_parity_adjustment(
    scores=[85, 78, 92, 65],
    protected_attrs=["male", "female", "male", "female"],
    target_parity_threshold=0.9
)

# Blind resume processing
blinded, removed = BiasMitigator.blind_resume_processing(
    resume_data,
    blind_level="standard"  # or "minimal", "maximum"
)
```

#### Audit Logging (`app/middlewares/audit_logger.py`)
```python
from app.middlewares.audit_logger import AuditLogger

# Log candidate screening
AuditLogger.log_candidate_screening(
    candidate_id="uuid",
    session_id="session_uuid",
    score=85.5,
    bias_detected=False
)

# Log hiring decision
AuditLogger.log_decision(
    application_id="APP-12345",
    candidate_id="uuid",
    decision="accepted",
    reason="Strong technical skills match"
)
```

## ☁️ Deployment

### Docker

```bash
# Build image
docker build -t trustlens-backend .

# Run container
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://... \
  -e FIREBASE_KEY='{"type":"service_account",...}' \
  trustlens-backend
```

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy trustlens-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql://...,FIREBASE_KEY=secret"
```

## 📊 Monitoring

### Health Checks
- `/health` - Application health (fast)
- `/ready` - Database connectivity check

### Logging
- Application logs: Standard Python logging
- Audit logs: `audit.log` file (JSON format)
- Request logs: Structured logging via middleware

### Metrics
Track via your monitoring solution:
- Request latency
- Error rates
- Bias detection frequency
- Fairness score trends

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards
- Follow PEP 8 style guide
- Add type hints to functions
- Write tests for new features
- Document API changes

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Hugging Face](https://huggingface.co/) - ML model hosting
- [Google Gemini](https://ai.google.dev/) - AI enhancement

---

**Built with ❤️ for fairer hiring practices**
