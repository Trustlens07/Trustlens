---
title: ML Resume Service API
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# ML Resume Service API

**AI‑powered resume parsing, scoring, bias detection, and explainable reports** – served as a FastAPI microservice.  
Supports both digital and scanned PDFs via OCR fallback, fairness redaction, statistical bias detection (t‑test), and optional Google Gemini enhancement.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Spaces-yellow)](https://huggingface.co/spaces)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 Features

- **Resume parsing** – Extract name, email, skills, experience (exact months), education, projects, certifications, languages, GitHub/LinkedIn/portfolio links.  
- **Two explainable scoring modes**  
  - *Baseline* – Semantic similarity using Sentence‑BERT (pure pre‑trained model, no rules).  
  - *Enhanced* – Rule‑based (60%) + **Google Gemini** contextual scoring (40%).  
- **Fairness engine** – Redact personal information (strict / balanced / custom).  
- **Bias detection** – Independent t‑test on gender groups (p‑value, group means, recommendation).  
- **OCR fallback** – Automatically uses OCR.space / Tesseract for scanned/image‑based PDFs.  
- **Internship & job‑hopping detection** – Flags internships and computes stability score (average tenure).  
- **Explainable AI** – Detailed candidate report (strengths, gaps, experience, stability, AI coach advice).  
- **Dynamic Gemini endpoints** – Extract skills from job description, generate interview questions, cultural fit, summarise, rank candidates, adjust weights, write feedback emails.  
- **Zero‑training, zero‑labelling** – Works immediately for any domain (tech, medical, legal, creative).  

---

## 🚀 Live API

- **Base URL:** `https://preeee-276-ml-service-api.hf.space`  
- **Interactive docs:** [https://preeee-276-ml-service-api.hf.space/docs](https://preeee-276-ml-service-api.hf.space/docs)

---

## 📚 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | Service information (version, Gemini status) | No |
| `GET` | `/health` | Health check | No |
| `POST` | `/parse` | Upload a resume → returns structured `parsed_data` + raw text preview | No |
| `POST` | `/score` | Score a candidate (baseline or enhanced) | No |
| `POST` | `/score/compare` | Compare baseline vs enhanced on the same resume | No |
| `POST` | `/candidate-report` | Detailed, human‑readable report  | No |
| `POST` | `/bias/detect` | Statistical bias detection across a group of candidates | No |
| `GET` | `/skills` | List all skills (for autocomplete) | No |
| `POST` | `/gemini/explain-score` | Explain difference between baseline and enhanced score | No |
| `POST` | `/gemini/extract-skills` | Convert job description to required skills list | No |
| `POST` | `/gemini/summarise` | Generate a 2‑3 sentence professional summary | No |
| `POST` | `/gemini/adjust-weights` | Recommend scoring weights from job description | No |
| `POST` | `/gemini/feedback` | Generate a short, professional feedback email | No |

---

## ⚙️ Setup & Local Development

### Prerequisites

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (for local OCR – optional, fallback works without it)
- [Poppler](https://poppler.freedesktop.org/) (for pdf2image – required only if using local Tesseract)

### Installation

```bash
# Clone the repository
git clone https://huggingface.co/spaces/Preeee-276/ml-service-api
cd ml-service-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional, for Gemini)
export GEMINI_API_KEY="your_key_here"          # Linux/macOS
set GEMINI_API_KEY=your_key_here               # Windows

# Start the server
python ml_service.py
