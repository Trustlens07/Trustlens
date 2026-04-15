---
title: ML Resume Service

colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
license: mit
---

# ML Resume Service

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| POST | `/parse` | Parse resume |
| POST | `/score` | Score candidate |
| POST | `/score/compare` | Compare baseline vs enhanced |
| POST | `/bias/detect` | Bias detection |

## Google Services Used

- **Gemini AI** - Enhanced scoring mode
- **Document AI** - OCR for scanned PDFs

## Quick Test

```python
import requests
BASE = "https://preeee-276-ml-service-api.hf.space"
response = requests.get(f"{BASE}/health")
print(response.json())
