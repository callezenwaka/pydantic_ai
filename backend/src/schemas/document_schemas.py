# backend/src/schemas/document_schemas.py
"""
Document API schemas - Request/Response validation and serialization
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..models.document_model import ProcessingResult, ProcessingMetadata, DocumentType, ExtractionMethod

class ProcessingRequest(BaseModel):
    """API request schema for document processing"""
    webhook_url: Optional[str] = None
    output_format: str = Field(default="json", pattern="^(json|csv|xml)$")
    confidence_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class BatchProcessingRequest(BaseModel):
    """API request schema for batch processing"""
    webhook_url: Optional[str] = None
    output_format: str = "json"
    max_files: int = Field(default=10, le=50)

class ExtractedDataSchema(BaseModel):
    """Schema for extracted document data in API responses"""
    raw_response: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields

class PipelineDataSchema(BaseModel):
    """Schema for pipeline integration data transfer"""
    document_id: str
    document_type: DocumentType
    confidence_score: float
    needs_human_review: bool
    extraction_method: ExtractionMethod
    processing_time: str
    extracted_fields: Dict[str, Any]
    metadata: ProcessingMetadata

class ErrorResponseSchema(BaseModel):
    """API error response schema"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None

class HealthCheckResponseSchema(BaseModel):
    """Health check API response schema"""
    status: str
    processor_ready: bool
    available_methods: List[str]
    available_model: List[str]

class DocumentListResponseSchema(BaseModel):
    """Document list API response schema"""
    documents: List[Dict[str, Any]]
    total: int
    limit: int
    skip: int
    has_more: bool