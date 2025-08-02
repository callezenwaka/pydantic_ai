# src/snap_ai/services/file_service.py
"""
File handling service
"""

from pathlib import Path
from ..models.document import FileInfo
from ..core.utils import extract_text_from_file

class FileService:
    """Service for handling file operations"""
    
    ALLOWED_TYPES = ['.txt', '.pdf', '.png', '.jpg', '.jpeg']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, filename: str, file_size: int) -> None:
        """Validate uploaded file"""
        
        if not filename:
            raise ValueError("No file selected")
        
        file_ext = Path(filename).suffix.lower()
        
        # Handle camera captures
        if filename.startswith('captured_image') and not file_ext:
            file_ext = '.jpg'
        
        if file_ext not in self.ALLOWED_TYPES:
            raise ValueError(f"File type {file_ext} not supported. Use: {', '.join(self.ALLOWED_TYPES)}")
        
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File size {file_size/1024/1024:.1f}MB exceeds limit of {self.MAX_FILE_SIZE/1024/1024}MB")
    
    def analyze_file(self, file_content: bytes, filename: str) -> FileInfo:
        """Analyze file and return file info"""
        
        file_size = len(file_content)
        self.validate_file(filename, file_size)
        
        file_ext = Path(filename).suffix.lower()
        is_camera_capture = filename.startswith('captured_image')
        
        # Handle camera captures
        if is_camera_capture and not file_ext:
            file_ext = '.jpg'
        
        return FileInfo(
            filename=filename,
            size_bytes=file_size,
            file_type=file_ext,
            is_camera_capture=is_camera_capture
        )
    
    async def save_temp_file(self, file_content: bytes, filename: str) -> Path:
        """Save file content to temporary file"""
        
        temp_dir = Path("uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Create unique filename
        import uuid
        unique_filename = f"{uuid.uuid4()}_{filename}"
        temp_path = temp_dir / unique_filename
        
        # Write with proper flushing
        with open(temp_path, "wb") as f:
            f.write(file_content)
            f.flush()
            import os
            os.fsync(f.fileno())
        
        return temp_path
    
    def extract_text(self, file_path: Path, file_type: str) -> str:
        """Extract text from file"""
        return extract_text_from_file(file_path, file_type)