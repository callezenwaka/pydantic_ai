# backend/src/schemas/workflow_schemas.py
"""
Workflow API schemas - Request/Response validation and serialization
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..models.workflow_model import WorkflowType, ExportFormat, WorkflowStatus, WebhookConfig

class WorkflowRequestSchema(BaseModel):
    """API request schema for workflow processing"""
    workflow_type: WorkflowType
    webhook_config: Optional[WebhookConfig] = None
    export_format: ExportFormat = ExportFormat.JSON
    metadata: Optional[Dict[str, Any]] = None

class WorkflowResponseSchema(BaseModel):
    """API response schema for workflow processing"""
    workflow_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class ExportRequestSchema(BaseModel):
    """API request schema for export operations"""
    result_id: str
    format: ExportFormat
    include_metadata: bool = True
    custom_fields: Optional[List[str]] = None

class WorkflowStatusResponseSchema(BaseModel):
    """API response schema for workflow status"""
    workflow_id: str
    status: str
    last_updated: str

class WorkflowTypesResponseSchema(BaseModel):
    """API response schema for available workflow types"""
    workflow_types: List[Dict[str, str]]

class WorkflowConfigurationResponseSchema(BaseModel):
    """API response schema for workflow configuration"""
    configuration_id: str
    status: str

class SupportedFormatsResponseSchema(BaseModel):
    """API response schema for supported formats"""
    supported_formats: List[str]
    max_file_size_mb: int
    export_formats: List[str]

class SystemLimitsResponseSchema(BaseModel):
    """API response schema for system limits"""
    max_file_size_mb: int
    max_batch_files: int
    supported_formats: List[str]
    rate_limits: Dict[str, int]