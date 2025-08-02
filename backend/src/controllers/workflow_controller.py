# src/snap_ai/controllers/workflow_controller.py
"""
Workflow controller - Handles workflow integration endpoints
"""

from typing import Optional
from fastapi import UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, Response

from ..services.workflow_service import WorkflowService
from ..models.workflow_model import WorkflowType, ExportFormat, WorkflowStatus


class WorkflowController:
    """Controller for workflow integration endpoints"""
    
    def __init__(self):
        pass
    
    async def process_and_forward_api(
        self, 
        file: UploadFile, 
        webhook_url: Optional[str], 
        workflow_type: str,
        workflow_service: WorkflowService
    ) -> dict:
        """API endpoint to process and forward to webhook"""
        try:
            file_content = await file.read()
            workflow_type_enum = WorkflowType(workflow_type)
            
            result = await workflow_service.process_and_forward(
                file_content, 
                file.filename,
                workflow_type_enum,
                webhook_url
            )
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def export_result_api(
        self, 
        result_id: str, 
        format: str,
        workflow_service: WorkflowService
    ) -> Response:
        """API endpoint to export results in different formats"""
        try:
            export_format = ExportFormat(format)
            content, media_type, filename = await workflow_service.export_result(
                result_id, 
                export_format
            )
            
            return Response(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def workflow_status_api(
        self, 
        workflow_id: str,
        workflow_service: WorkflowService
    ) -> dict:
        """API endpoint to check workflow status"""
        try:
            status = await workflow_service.get_workflow_status(workflow_id)
            if not status:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return status
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def available_types_api(self, workflow_service: WorkflowService) -> dict:
        """API endpoint to get available workflow types"""
        try:
            types = workflow_service.get_available_workflow_types()
            return {"workflow_types": types}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def configure_workflow_api(
        self, 
        workflow_config: dict,
        workflow_service: WorkflowService
    ) -> dict:
        """API endpoint to configure workflow settings"""
        try:
            config_id = await workflow_service.configure_workflow(workflow_config)
            return {"configuration_id": config_id, "status": "configured"}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
