# src/snap_ai/routes/workflow_routes.py
"""
Workflow routes - Workflow integration endpoint definitions
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Query
from fastapi.responses import Response

from ..controllers.workflow_controller import WorkflowController
from ..dependencies.workflow_dependencies import get_workflow_service
from ..models.workflow_model import WorkflowType, ExportFormat

router = APIRouter()
controller = WorkflowController()

@router.post("/api/workflow/webhook")
async def process_and_forward(
    file: UploadFile = File(...),
    workflow_type: str = Form(...),
    webhook_url: Optional[str] = Form(None),
    workflow_service = Depends(get_workflow_service)
):
    """Process document and forward to webhook"""
    return await controller.process_and_forward_api(
        file, webhook_url, workflow_type, workflow_service
    )

@router.get("/api/workflow/export/{result_id}")
async def export_result(
    result_id: str,
    format: str = Query(default="json", regex="^(json|csv|xml)$"),
    workflow_service = Depends(get_workflow_service)
):
    """Export results in different formats"""
    return await controller.export_result_api(result_id, format, workflow_service)

@router.get("/api/workflow/status/{workflow_id}")
async def workflow_status(
    workflow_id: str,
    workflow_service = Depends(get_workflow_service)
):
    """Check workflow status"""
    return await controller.workflow_status_api(workflow_id, workflow_service)

@router.get("/api/workflow/types")
async def available_types(
    workflow_service = Depends(get_workflow_service)
):
    """Get available workflow types"""
    return await controller.available_types_api(workflow_service)

@router.post("/api/workflow/configure")
async def configure_workflow(
    workflow_config: dict,
    workflow_service = Depends(get_workflow_service)
):
    """Configure workflow settings"""
    return await controller.configure_workflow_api(workflow_config, workflow_service)

# Additional utility endpoints
@router.get("/api/supported-formats")
async def supported_formats():
    """Get supported file formats"""
    return {
        "supported_formats": [".txt", ".pdf", ".png", ".jpg", ".jpeg"],
        "max_file_size_mb": 10,
        "export_formats": ["json", "csv", "xml"]
    }

@router.get("/api/limits")
async def system_limits():
    """Get system limits"""
    return {
        "max_file_size_mb": 10,
        "max_batch_files": 50,
        "supported_formats": [".txt", ".pdf", ".png", ".jpg", ".jpeg"],
        "rate_limits": {
            "requests_per_minute": 60,
            "batch_requests_per_hour": 100
        }
    }