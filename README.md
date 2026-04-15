---
title: ML Resume Service API
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---
# ML Resume Service API

A production‑ready machine learning service for resume parsing, candidate scoring, bias detection, and explainable AI. Built with FastAPI and deployed on Hugging Face Spaces.

##  Live API

Base URL: `https://preeee-276-ml-service-api.hf.space`

Interactive documentation: [https://preeee-276-ml-service-api.hf.space/docs](https://preeee-276-ml-service-api.hf.space/docs)

##  Features

- **Resume Parsing** – Extract name, email, skills, experience, education, projects, certifications, achievements, languages from PDF/DOCX (supports both digital and scanned documents via OCR fallback).
- **Smart Scoring** – Weighted scoring with customisable category weights (skills, experience, education, projects, soft skills).
- **Baseline vs Enhanced** – Compare pre‑trained model results with Gemini‑enhanced results.
- **Bias Detection** – Statistical t‑test to detect gender bias across a group of candidates.
- **Explainable AI** – Detailed candidate report with strengths, gaps, recommendations.
- **Fairness Engine** – Redact personal information (strict, balanced, or custom modes).
- **Gemini Integration** – Optional text cleaning and score boost using Google Gemini API.

##Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`

