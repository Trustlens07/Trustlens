---
title: ML Resume Service API
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# ML Resume Service API

A production‑ready machine learning service for resume parsing, candidate scoring, bias detection, and explainable AI. Built with FastAPI and deployed on Hugging Face Spaces.

# Live API

**Base URL:** `https://preeee-276-ml-service-api.hf.space`  
**Interactive docs:** [https://preeee-276-ml-service-api.hf.space/docs](https://preeee-276-ml-service-api.hf.space/docs)

#  API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service information (version, Gemini status) |
| `GET` | `/health` | Health check – returns status and Gemini availability |
| `POST` | `/parse` | Upload a resume (PDF/DOCX) → returns structured `parsed_data` |
| `POST` | `/score` | Score a candidate – returns score, matched/missing skills, short explanation |
| `POST` | `/score/compare` | Compare baseline (pre‑trained only) vs enhanced (with Gemini) |
| `POST` | `/candidate-report` | Detailed, human‑readable report for candidate login |
| `POST` | `/bias/detect` | Statistical bias detection (t‑test) across a group of candidates |
| `GET` | `/skills` | List all known skills (for autocomplete) |

