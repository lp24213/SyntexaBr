# 📁 File Upload Validation
# Migrado de production-node/api/src/index.js para vereda_backend

import os
import logging
from pathlib import Path
from uuid import uuid4
from vereda_backend.core.security_config import ALLOWED_MIME_TYPES, ALLOWED_EXTENSIONS, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

class FileValidator:
    """Validate uploaded files: MIME type, extension, path traversal"""
    
    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = Path(upload_dir or os.getenv("UPLOAD_DIR", "/data/uploads"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(self, filename: str, mimetype: str, file_size: int) -> tuple[bool, str | None]:
        """
        Validate filename, MIME type, file size, extension.
        Returns (is_valid, error_message)
        """
        
        # ✅ Check file size
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large: {file_size} > {MAX_FILE_SIZE} bytes"
        
        # ✅ Check MIME type (whitelist)
        if mimetype not in ALLOWED_MIME_TYPES:
            logger.warning(f"❌ MIME type rejected: {mimetype}")
            return False, f"MIME type not allowed: {mimetype}"
        
        # ✅ Check extension (whitelist)
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"❌ Extension rejected: {ext}")
            return False, f"Extension not allowed: {ext}"
        
        return True, None
    
    def sanitize_filename(self, original_filename: str) -> str:
        """
        Sanitize filename to prevent path traversal & injection.
        Returns: SAFE_TIMESTAMP-UUID.ext
        """
        # ✅ Remove any directory components (path traversal protection)
        safe_name = Path(original_filename).name
        
        # ✅ Remove any suspicious characters
        safe_name = "".join(c if c.isalnum() or c in ".-_" else "_" for c in safe_name)
        
        # ✅ Generate UUID-based filename
        ext = Path(safe_name).suffix.lower() or ".bin"
        timestamp = int(__import__("time").time() * 1000)
        
        return f"{timestamp}-{uuid4()}{ext}"
    
    def get_safe_path(self, sanitized_filename: str) -> tuple[Path, bool]:
        """
        Get safe file path. Verify it's within upload_dir (prevent path traversal).
        Returns (safe_path, is_valid)
        """
        target_path = self.upload_dir / sanitized_filename
        
        # ✅ Verify path is within upload_dir (prevent path traversal like ../../../etc/passwd)
        try:
            target_path.resolve().relative_to(self.upload_dir.resolve())
        except ValueError:
            logger.error(f"❌ Path traversal attempt detected: {target_path}")
            return target_path, False
        
        return target_path, True
    
    async def save_file(self, upload_file, original_filename: str) -> tuple[str | None, str | None]:
        """
        Save uploaded file safely.
        Returns (file_path, error_message)
        """
        
        # ✅ Validate
        is_valid, error = self.validate(
            original_filename,
            upload_file.content_type or "application/octet-stream",
            len(upload_file.file.read()) if hasattr(upload_file.file, 'read') else 0
        )
        
        if not is_valid:
            return None, error
        
        # ✅ Sanitize filename
        safe_filename = self.sanitize_filename(original_filename)
        
        # ✅ Get safe path
        safe_path, is_safe = self.get_safe_path(safe_filename)
        if not is_safe:
            return None, "Invalid file path"
        
        # ✅ Save file
        try:
            upload_file.file.seek(0)  # Reset file pointer
            with open(safe_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)
            
            logger.info(f"✅ File saved: {safe_filename}")
            return str(safe_path), None
        
        except Exception as e:
            logger.error(f"❌ File save error: {e}")
            return None, f"Failed to save file: {str(e)}"
