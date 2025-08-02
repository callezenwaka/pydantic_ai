# backend/src/models/document_model.py
"""
Document core models - Business entities and data structures
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum

# Core Enums
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

# Core Models
class FileInfo(BaseModel):
    """File information model"""
    filename: str
    size_bytes: int
    file_type: str
    is_camera_capture: bool = False

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

class BatchProcessingResult(BaseModel):
    """Batch processing result"""
    batch_id: str
    total_documents: int
    successful: int
    failed: int
    results: List[ProcessingResult]
    processed_at: float