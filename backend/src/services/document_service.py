# src/snap_ai/services/document_service.py
"""
Document service - Business logic for document processing
"""

import uuid
import time
from typing import Dict, Any, List, Optional, Tuple

from ..models.document_model import (
    ProcessingResult, 
    BatchProcessingResult, 
    FileInfo, 
    DocumentType
)
from ..core.processor import Processor
from ..core.storage import StorageClient
from ..core.textract_core import extract_text_from_file


class FileHandler:
    """File handling utilities"""
    
    ALLOWED_TYPES = ['.txt', '.pdf', '.png', '.jpg', '.jpeg']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, filename: str, file_size: int) -> None:
        """Validate uploaded file"""
        from pathlib import Path
        
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
        from pathlib import Path
        
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
    
    async def save_temp_file(self, file_content: bytes, filename: str):
        """Save file content to temporary file"""
        from pathlib import Path
        import uuid
        import os
        
        temp_dir = Path("uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Create unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        temp_path = temp_dir / unique_filename
        
        # Write with proper flushing
        with open(temp_path, "wb") as f:
            f.write(file_content)
            f.flush()
            os.fsync(f.fileno())
        
        return temp_path


class DocumentService:
    """Service for document processing business logic"""
    
    def __init__(self, processor: Processor, storage_client: StorageClient):
        self.processor = processor
        self.storage_client = storage_client
        self.file_handler = FileHandler()
    
    async def quick_scan(
        self, 
        file_content: bytes, 
        filename: str
    ) -> ProcessingResult:
        """Quick scan: upload → process → remove"""
        
        # Validate and analyze file
        file_info = self.file_handler.analyze_file(file_content, filename)
        
        # Save file temporarily
        temp_path = await self.file_handler.save_temp_file(file_content, filename)
        
        try:
            # Extract text
            text = extract_text_from_file(temp_path, file_info.file_type)
            
            # Process with AI (synchronous call)
            raw_result = self.processor.process_document(text)
            
            # Convert to structured result
            result = self._convert_to_processing_result(raw_result, file_info)
            
            return result
            
        finally:
            # Clean up temp file (quick scan removes file)
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
    
    async def document_workflow(
        self, 
        file_content: bytes, 
        filename: str
    ) -> Dict[str, Any]:
        """Document workflow: upload → process → store"""
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Validate and analyze file
        file_info = self.file_handler.analyze_file(file_content, filename)
        
        # Save file temporarily for processing
        temp_path = await self.file_handler.save_temp_file(file_content, filename)
        
        try:
            # Extract text
            text = extract_text_from_file(temp_path, file_info.file_type)
            
            # Process with AI (synchronous call)
            raw_result = self.processor.process_document(text)
            
            # Convert to structured result
            processing_result = self._convert_to_processing_result(raw_result, file_info)
            
            # Store file to Google Cloud Storage
            storage_path = f"documents/{document_id}/{filename}"
            storage_location = await self.storage_client.upload_file(
                file_content, 
                storage_path,
                file_info.file_type
            )
            
            # Store metadata
            metadata = {
                "document_id": document_id,
                "original_filename": filename,
                "storage_location": storage_location,
                "processing_result": processing_result.dict(),
                "uploaded_at": time.time(),
                "file_info": file_info.dict()
            }
            
            await self.storage_client.store_metadata(document_id, metadata)
            
            # Generate access URL
            access_url = await self.storage_client.get_signed_url(storage_path)
            
            return {
                "document_id": document_id,
                "processing_result": processing_result,
                "storage_location": storage_location,
                "access_url": access_url
            }
            
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
    
    async def batch_quick_scan(
        self, 
        files_data: List[Tuple[bytes, str]]
    ) -> BatchProcessingResult:
        """Batch quick scan processing"""
        
        batch_id = str(uuid.uuid4())
        results = []
        
        for i, (file_content, filename) in enumerate(files_data):
            try:
                result = await self.quick_scan(file_content, filename)
                # Add batch index if needed
                if hasattr(result, 'batch_index'):
                    result.batch_index = i
                results.append(result)
                
            except Exception as e:
                error_result = ProcessingResult(
                    document_type=DocumentType.UNKNOWN,
                    ml_confidence=0.0,
                    overall_confidence=0.0,
                    confidence_level="low",
                    extraction_method="none",
                    model_display_name="Error",
                    processing_time="0s",
                    needs_human_review=True,
                    extracted_data={"error": str(e)},
                    uploaded_file=filename
                )
                if hasattr(error_result, 'batch_index'):
                    error_result.batch_index = i
                results.append(error_result)
        
        return BatchProcessingResult(
            batch_id=batch_id,
            total_documents=len(files_data),
            successful=len([r for r in results if "error" not in r.extracted_data]),
            failed=len([r for r in results if "error" in r.extracted_data]),
            results=results,
            processed_at=time.time()
        )
    
    async def batch_document_workflow(
        self, 
        files_data: List[Tuple[bytes, str]]
    ) -> Dict[str, Any]:
        """Batch document workflow processing"""
        
        batch_id = str(uuid.uuid4())
        results = []
        
        for i, (file_content, filename) in enumerate(files_data):
            try:
                result = await self.document_workflow(file_content, filename)
                result["batch_index"] = i
                results.append(result)
                
            except Exception as e:
                error_result = {
                    "batch_index": i,
                    "filename": filename,
                    "error": str(e),
                    "document_id": None
                }
                results.append(error_result)
        
        successful = len([r for r in results if "error" not in r])
        failed = len([r for r in results if "error" in r])
        
        return {
            "batch_id": batch_id,
            "total_documents": len(files_data),
            "successful": successful,
            "failed": failed,
            "results": results,
            "processed_at": time.time()
        }
    
    async def list_stored_documents(
        self, 
        limit: int = 100, 
        skip: int = 0
    ) -> Dict[str, Any]:
        """List stored documents with pagination"""
        
        documents = await self.storage_client.list_documents(limit=limit, skip=skip)
        total_count = await self.storage_client.count_documents()
        
        return {
            "documents": documents,
            "total": total_count,
            "limit": limit,
            "skip": skip,
            "has_more": skip + limit < total_count
        }
    
    async def get_stored_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get specific stored document"""
        return await self.storage_client.get_document_metadata(document_id)
    
    async def delete_stored_document(self, document_id: str) -> bool:
        """Delete stored document and its files"""
        
        # Get document metadata
        metadata = await self.storage_client.get_document_metadata(document_id)
        if not metadata:
            return False
        
        # Delete file from storage
        storage_location = metadata.get("storage_location")
        if storage_location:
            await self.storage_client.delete_file(storage_location)
        
        # Delete metadata
        await self.storage_client.delete_metadata(document_id)
        
        return True
    
    def _convert_to_processing_result(
        self, 
        raw_result: Dict[str, Any], 
        file_info: FileInfo
    ) -> ProcessingResult:
        """Convert raw processor result to structured ProcessingResult"""
        
        return ProcessingResult(
            document_type=DocumentType(raw_result.get("document_type", "unknown")),
            ml_confidence=raw_result.get("ml_confidence", 0.0),
            overall_confidence=raw_result.get("overall_confidence", 0.0),
            confidence_level=raw_result.get("confidence_level", "low"),
            extraction_method=raw_result.get("extraction_method", "none"),
            model_display_name=raw_result.get("model_display_name", "Unknown"),
            processing_time=raw_result.get("processing_time", "0s"),
            needs_human_review=raw_result.get("needs_human_review", True),
            extracted_data=raw_result.get("extracted_data", {}),
            uploaded_file=file_info.filename,
            file_size=file_info.size_bytes,
            file_type=file_info.file_type,
            raw_text=raw_result.get("raw_text")
        )