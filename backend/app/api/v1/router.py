from fastapi import APIRouter
from app.api.v1.endpoints import upload, candidates, scores, bias, feedback, enhance

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
api_router.include_router(enhance.router, prefix="/candidates", tags=["Enhancement"])
api_router.include_router(scores.router, prefix="/scores", tags=["Scores"])
api_router.include_router(bias.router, prefix="/bias", tags=["Bias Analysis"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])