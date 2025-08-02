# backend/src/dependencies/workflow_dependencies.py
"""
Workflow service dependencies
"""

from ..services.workflow_service import WorkflowService
from ..core.service_manager import get_processor, get_storage_client

def get_workflow_service() -> WorkflowService:
    """Dependency injection for workflow service"""
    processor = get_processor()
    storage_client = get_storage_client()
    return WorkflowService(processor, storage_client)