# src/snap_ai/dependencies/__init__.py
"""
Dependencies package - FastAPI dependency injection
"""

from .document_dependencies import get_document_service
from .workflow_dependencies import get_workflow_service

__all__ = [
    "get_document_service",
    "get_workflow_service"
]
