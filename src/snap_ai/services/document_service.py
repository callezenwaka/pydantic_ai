# src/snap_ai/services/document_service.py
"""
Document processing service - Business logic layer
"""

import uuid
import time
from typing import Dict, Any, List, Optional

from ..models.document import (
    ProcessingMetadata, 
    ProcessingResult, 
    ProcessingRequest,
    BatchProcessingResult, 
    FileInfo, 
    PipelineData, 
    DocumentType
)
from ..core.processor import Processor
from .file_service import FileService

class DocumentProcessingService:
    """Service for handling document processing business logic"""
    
    def __init__(self, processor: Processor):
        self.processor = processor
        self.file_service = FileService()
    
    async def process_single_document(
        self, 
        file_content: bytes, 
        filename: str, 
        request_params: Optional[ProcessingRequest] = None
    ) -> ProcessingResult:
        """Process a single document"""
        
        # Get file info
        file_info = self.file_service.analyze_file(file_content, filename)
        
        # Save file temporarily
        temp_path = await self.file_service.save_temp_file(file_content, filename)
        
        try:
            # Extract text
            text = self.file_service.extract_text(temp_path, file_info.file_type)
            
            # Process with AI
            raw_result = self.processor.process_document(text)
            
            # Convert to structured result
            result = self._convert_to_processing_result(raw_result, file_info)
            
            return result
            
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
    
    async def process_batch_documents(
        self, 
        files_data: List[tuple], 
        request_params: Optional[BatchProcessingResult] = None
    ) -> BatchProcessingResult:
        """Process multiple documents in batch"""
        
        batch_id = str(uuid.uuid4())
        results = []
        
        for i, (file_content, filename) in enumerate(files_data):
            try:
                result = await self.process_single_document(file_content, filename)
                result.batch_index = i
                results.append(result)
                
            except Exception as e:
                # Add error result
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
    
    def format_for_pipeline(self, result: ProcessingResult) -> PipelineData:
        """Format processing result for pipeline integration"""
        
        return PipelineData(
            document_id=str(uuid.uuid4()),
            document_type=result.document_type,
            confidence_score=result.overall_confidence,
            needs_human_review=result.needs_human_review,
            extraction_method=result.extraction_method,
            processing_time=result.processing_time,
            extracted_fields=result.extracted_data,
            metadata=ProcessingMetadata(
                document_id=str(uuid.uuid4()),
                processed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                processor_version="1.0.0",
                extraction_method=result.extraction_method
            )
        )
    
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