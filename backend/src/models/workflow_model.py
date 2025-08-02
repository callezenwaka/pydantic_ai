# backend/src/models/workflow_model.py
"""
Workflow core models - Business entities and data structures
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum

# Core Enums
class WorkflowType(str, Enum):
    QUICK_SCAN = "quick_scan"
    DOCUMENT_WORKFLOW = "document_workflow"

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Core Models
class WebhookConfig(BaseModel):
    """Webhook configuration model"""
    url: str
    headers: Optional[Dict[str, str]] = None
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)

class WorkflowConfiguration(BaseModel):
    """Workflow configuration model"""
    name: str
    workflow_type: WorkflowType
    default_webhook: Optional[WebhookConfig] = None
    processing_options: Optional[Dict[str, Any]] = None
    storage_settings: Optional[Dict[str, Any]] = None
    enabled: bool = True

class WorkflowExecution(BaseModel):
    """Workflow execution model"""
    workflow_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None