# src/snap_ai/models/document.py
"""
Document processing data models and schemas
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    FORM = "form"
    RECEIPT = "receipt"
    UNKNOWN = "unknown"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ExtractionMethod(str, Enum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"

class ProcessingRequest(BaseModel):
    """Request model for document processing"""
    webhook_url: Optional[str] = None
    output_format: str = Field(default="json", pattern="^(json|csv|xml)$")
    confidence_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class FileInfo(BaseModel):
    """File information model"""
    filename: str
    size_bytes: int
    file_type: str
    is_camera_capture: bool = False

class ExtractedData(BaseModel):
    """Base model for extracted document data"""
    raw_response: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields

class ProcessingMetadata(BaseModel):
    """Processing metadata"""
    document_id: str
    processed_at: str
    processor_version: str = "1.0.0"
    extraction_method: ExtractionMethod
    processing_time: str

class ProcessingResult(BaseModel):
    """Complete document processing result"""
    # Document classification
    document_type: DocumentType
    ml_confidence: float = Field(ge=0.0, le=1.0)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    
    # Processing info
    extraction_method: ExtractionMethod
    model_display_name: str
    processing_time: str
    
    # Review requirements
    needs_human_review: bool
    
    # Data
    extracted_data: Dict[str, Any]
    
    # File info
    uploaded_file: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    
    # Raw text (for debugging)
    raw_text: Optional[str] = None

class BatchProcessingRequest(BaseModel):
    """Batch processing request"""
    webhook_url: Optional[str] = None
    output_format: str = "json"
    max_files: int = Field(default=10, le=50)

class BatchProcessingResult(BaseModel):
    """Batch processing result"""
    batch_id: str
    total_documents: int
    successful: int
    failed: int
    results: List[ProcessingResult]
    processed_at: float

class PipelineData(BaseModel):
    """Formatted data for pipeline integration"""
    document_id: str
    document_type: DocumentType
    confidence_score: float
    needs_human_review: bool
    extraction_method: ExtractionMethod
    processing_time: str
    extracted_fields: Dict[str, Any]
    metadata: ProcessingMetadata

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None