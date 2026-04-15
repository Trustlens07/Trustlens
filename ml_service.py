# ml_service.py - FINAL WITH RELIABLE OCR
# Uses OCR.space API (free) as primary, falls back to Tesseract if needed

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import re
import io
import base64
import requests
import PyPDF2
import docx
import numpy as np
from scipy import stats
import google.generativeai as genai
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

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

# OCR.space API (free, no key needed for 500 requests/month)
OCR_SPACE_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "")  # optional, get free key for higher limits
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

app = FastAPI(title="ML Resume Service", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# PYDANTIC SCHEMAS (keep your existing ones – not repeated for brevity)
# ============================================
# ... (insert all your schema classes here – they are unchanged)
# To save space, I'll assume you have them. If not, copy from the previous complete message.

# ============================================
# FAIRNESS ENGINE (unchanged)
# ============================================
# ... (insert FairnessEngine)

# ============================================
# DOCUMENT EXTRACTION (with reliable OCR)
# ============================================

class DocumentExtractor:
    @staticmethod
    def extract_baseline(file_bytes: bytes, file_type: str) -> str:
        if file_type == "pdf":
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                text = " ".join([page.extract_text() or "" for page in reader.pages])
                if len(text.strip()) > 100:
                    return text
            except:
                pass
            return ""
        else:
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                return " ".join([p.text for p in doc.paragraphs])
            except:
                return ""

    @staticmethod
    def extract_with_ocr_space(file_bytes: bytes) -> str:
        """Use OCR.space API – works for scanned PDFs."""
        try:
            encoded = base64.b64encode(file_bytes).decode('utf-8')
            payload = {
                'base64Image': f'data:application/pdf;base64,{encoded}',
                'language': 'eng',
                'filetype': 'PDF',
                'isOverlayRequired': False,
                'scale': True,
                'OCREngine': 2
            }
            if OCR_SPACE_API_KEY:
                payload['apikey'] = OCR_SPACE_API_KEY
            response = requests.post('https://api.ocr.space/parse/image', data=payload, timeout=60)
            result = response.json()
            if result.get('IsErroredOnProcessing'):
                error_msg = result.get('ErrorMessage', ['Unknown error'])[0]
                print(f"OCR.space error: {error_msg}")
                return ""
            parsed_text = []
            for page in result.get('ParsedResults', []):
                parsed_text.append(page.get('ParsedText', ''))
            return "\n".join(parsed_text)
        except Exception as e:
            print(f"OCR.space exception: {e}")
            return ""

    @staticmethod
    def extract_with_tesseract(file_bytes: bytes) -> str:
        """Local Tesseract OCR – requires poppler and tesseract installed."""
        try:
            images = convert_from_bytes(file_bytes, dpi=300)
            full_text = []
            for img in images:
                img = img.convert('L')
                text = pytesseract.image_to_string(img, lang='eng')
                full_text.append(text)
            return "\n".join(full_text)
        except Exception as e:
            print(f"Tesseract OCR failed: {e}")
            return ""

    @staticmethod
    def extract_enhanced(file_bytes: bytes, file_type: str) -> str:
        if file_type != "pdf":
            return DocumentExtractor.extract_baseline(file_bytes, file_type)
        
        # Try direct extraction (digital PDFs)
        text = DocumentExtractor.extract_baseline(file_bytes, file_type)
        if text and len(text.strip()) > 200:
            print("Direct extraction successful")
            return text
        
        # Try pdfplumber (handles tables better)
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            text += " ".join([str(cell) for cell in row if cell]) + " "
                if len(text.strip()) > 200:
                    print("pdfplumber extraction successful")
                    return text
        except Exception as e:
            print(f"pdfplumber error: {e}")
        
        # Fallback to OCR.space
        print("Trying OCR.space API...")
        text = DocumentExtractor.extract_with_ocr_space(file_bytes)
        if text and len(text.strip()) > 100:
            print("OCR.space extraction successful")
            return text
        
        # Last resort: local Tesseract
        print("Trying local Tesseract...")
        text = DocumentExtractor.extract_with_tesseract(file_bytes)
        if text and len(text.strip()) > 100:
            print("Tesseract extraction successful")
            return text
        
        print("All extraction methods failed")
        return ""

# ============================================
# RESUME PARSER, SCORING ENGINE, ENDPOINTS – unchanged from your previous working version
# ============================================
# ... (insert your existing ResumeParser, ScoringEngine, generate_detailed_report, and all endpoints)
# They are exactly the same as in the previous complete message.

# ============================================
# API ENDPOINTS (same as before)
# ============================================
# ... (insert your endpoints)

if __name__ == "__main__":
    import uvicorn
    print("\n✅ ML Resume Service - Multi‑layer OCR")
    print(f"Gemini: {'enabled' if GEMINI_AVAILABLE else 'disabled'}")
    uvicorn.run(app, host="0.0.0.0", port=7860)