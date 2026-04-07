from fastapi import HTTPException, UploadFile
from app.core.config import settings
import os
import mimetypes

class FileValidator:
    @staticmethod
    def validate_file(file: UploadFile):
        """Validate uploaded file"""
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # Check MIME type
        file_content = file.file.read(1024)  # Read first 1KB for MIME detection
        file.file.seek(0)  # Reset to beginning

        # Prefer python-magic if available, otherwise fall back to mimetypes.
        mime = None
        try:
            import magic  # type: ignore
            mime = magic.from_buffer(file_content, mime=True)
        except Exception:
            mime = mimetypes.guess_type(file.filename)[0]
            if mime is None:
                # As a last resort, infer from extension.
                mime = FileValidator.get_content_type(file.filename)

        allowed_mimes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        if mime not in allowed_mimes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file content. Detected MIME type: {mime}"
            )
        
        return True
    
    @staticmethod
    def get_content_type(filename: str) -> str:
        """Get content type based on file extension"""
        extension = os.path.splitext(filename)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return content_types.get(extension, 'application/octet-stream')