---
title: ML Resume Service Phase 3
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# ML Resume Service - Phase 3

## Features
- ✅ ML Scoring Model (Random Forest)
- ✅ LRU Caching for faster parsing
- ✅ Statistical Bias Detection (t-test)
- ✅ Performance Metrics

## API Endpoints
- `GET /health` - Health check
- `POST /parse` - Parse resume with caching
- `POST /score` - Score candidate (rule-based or ML)
- `POST /bias/detect` - Detect hiring bias
- `GET /cache/stats` - Cache statistics
- `GET /model/info` - Model information

## Usage
Check the `/docs` endpoint for interactive API documentation.