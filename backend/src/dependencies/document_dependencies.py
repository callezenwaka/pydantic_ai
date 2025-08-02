# backend/src/dependencies/document_dependencies.py

"""
Document service dependencies
"""

from ..services.document_service import DocumentService
from ..core.service_manager import get_processor, get_storage_client

def get_document_service() -> DocumentService:
    """Dependency injection for document service"""
    processor = get_processor()
    storage_client = get_storage_client()
    return DocumentService(processor, storage_client)