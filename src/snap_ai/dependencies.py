# src/snap_ai/dependencies.py
"""
FastAPI dependencies for dependency injection
"""

from typing import Optional
from fastapi import HTTPException

from .core.processor import Processor
from .services.document_service import DocumentProcessingService

# Global instances
_processor: Optional[Processor] = None
_document_service: Optional[DocumentProcessingService] = None

def initialize_services():
    """Initialize all services on startup"""
    global _processor, _document_service
    
    try:
        _processor = Processor()
        _document_service = DocumentProcessingService(_processor)
        print("✅ All services initialized")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        raise e

def cleanup_services():
    """Cleanup services on shutdown"""
    global _processor, _document_service
    
    print("🔄 Shutting down services...")
    _processor = None
    _document_service = None

def get_processor() -> Processor:
    """Dependency to get processor instance"""
    if _processor is None:
        raise HTTPException(status_code=503, detail="Processor not initialized")
    return _processor

def get_document_service() -> DocumentProcessingService:
    """Dependency to get document service instance"""
    if _document_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    return _document_service