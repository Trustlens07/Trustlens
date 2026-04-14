# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth as firebase_auth
import logging

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    logger.info(f"Received token (first 50 chars): {token[:50]}...")
    try:
        decoded_token = firebase_auth.verify_id_token(token, check_revoked=True)
        logger.info(f"Token verified successfully for UID: {decoded_token.get('uid')}")
        return decoded_token
    except firebase_auth.ExpiredIdTokenError:
        logger.error("Token has expired")
        raise HTTPException(status_code=403, detail="Token has expired")
    except firebase_auth.InvalidIdTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=403, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        # Log full traceback to console
        logger.exception(f"Unexpected error verifying token: {str(e)}")
        raise HTTPException(status_code=403, detail=f"Auth error: {str(e)}")

@router.get("/test-token")
async def test_token(current_user: dict = Depends(get_current_user)):
    return {"message": "Token is valid", "uid": current_user.get("uid")}