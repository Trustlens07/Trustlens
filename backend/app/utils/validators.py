"""File validation and sanitization utilities."""

import magic
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates uploaded files for security and type compliance."""
    
    # MIME type to extension mapping
    ALLOWED_TYPES = {
        'application/pdf': '.pdf',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'text/plain': '.txt',
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file(file_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate file size, type, and name.
        
        Returns:
            Tuple of (is_valid: bool, message: str, safe_filename: Optional[str])
        """
        # Check file size
        if len(file_bytes) > FileValidator.MAX_FILE_SIZE:
            max_mb = FileValidator.MAX_FILE_SIZE / 1024 / 1024
            return False, f"File exceeds maximum size of {max_mb}MB", None
        
        # Check magic bytes (not just extension)
        try:
            detected = magic.from_buffer(file_bytes, mime=True)
        except Exception as e:
            logger.error(f"Magic detection failed: {e}")
            detected = None
        
        if detected not in FileValidator.ALLOWED_TYPES:
            allowed = ", ".join(FileValidator.ALLOWED_TYPES.values())
            return False, f"File type '{detected}' not allowed. Allowed: {allowed}", None
        
        # Sanitize filename
        safe_name = FileValidator._sanitize_filename(filename)
        if not safe_name:
            return False, "Invalid filename", None
        
        # Verify extension matches detected type
        expected_ext = FileValidator.ALLOWED_TYPES.get(detected)
        if expected_ext and not safe_name.lower().endswith(expected_ext):
            safe_name = safe_name + expected_ext
        
        logger.info(f"File validated: {safe_name} ({detected}, {len(file_bytes)} bytes)")
        return True, "Valid", safe_name
    
    @staticmethod
    def _sanitize_filename(filename: str) -> Optional[str]:
        """Sanitize filename to prevent directory traversal and other attacks."""
        if not filename:
            return None
        
        # Get just the filename, no path
        safe_name = Path(filename).name
        
        # Check for suspicious patterns
        dangerous_patterns = ['..', '/', '\\', '\x00', ';', '&', '|', '$', '`']
        for pattern in dangerous_patterns:
            if pattern in safe_name:
                logger.warning(f"Dangerous pattern '{pattern}' detected in filename: {filename}")
                return None
        
        # Remove control characters
        safe_name = ''.join(char for char in safe_name if ord(char) > 31)
        
        # Limit length
        if len(safe_name) > 255:
            safe_name = safe_name[:255]
        
        # Ensure it's not empty
        if not safe_name or safe_name == '.' or safe_name == '..':
            return None
        
        return safe_name
    
    @staticmethod
    def get_content_type(filename: str) -> str:
        """Get MIME content type from filename."""
        ext = Path(filename).suffix.lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
        }
        return mime_map.get(ext, 'application/octet-stream')


class InputSanitizer:
    """Sanitize user inputs to prevent injection attacks."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            return ""
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        value = ''.join(char for char in value if ord(char) > 31 or char in '\n\t\r')
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value.strip()
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and validate email format."""
        email = InputSanitizer.sanitize_string(email, max_length=254)
        
        # Basic email pattern check
        if '@' not in email or '.' not in email.split('@')[-1]:
            return ""
        
        return email.lower()
    
    @staticmethod
    def sanitize_uuid(value: str) -> Optional[str]:
        """Validate and return UUID string."""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if uuid_pattern.match(value):
            return value.lower()
        return None
