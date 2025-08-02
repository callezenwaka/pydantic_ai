# src/snap_ai/services/workflow_service.py
"""
Workflow service - Business logic for workflow orchestration
"""

import uuid
import json
import aiohttp
from typing import Dict, Any, Optional, Tuple, List

from ..models.workflow_model import WorkflowType, ExportFormat, WorkflowStatus
from ..core.processor import Processor
from ..core.storage import StorageClient


class WorkflowService:
    """Service for workflow orchestration and integration"""
    
    def __init__(self, processor: Processor, storage_client: StorageClient):
        self.processor = processor
        self.storage_client = storage_client
        self.active_workflows = {}  # In-memory workflow tracking
    
    async def process_and_forward(
        self, 
        file_content: bytes, 
        filename: str,
        workflow_type: WorkflowType,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process document and forward to webhook"""
        
        workflow_id = str(uuid.uuid4())
        
        try:
            # Update workflow status
            self.active_workflows[workflow_id] = WorkflowStatus.PROCESSING
            
            # Process based on workflow type
            if workflow_type == WorkflowType.QUICK_SCAN:
                # Quick scan workflow
                from .document_service import DocumentService
                doc_service = DocumentService(self.processor, self.storage_client)
                result = await doc_service.quick_scan(file_content, filename)
                
                response_data = {
                    "workflow_id": workflow_id,
                    "workflow_type": workflow_type.value,
                    "processing_result": result.dict(),
                    "forwarded": False
                }
                
            else:  # DOCUMENT_WORKFLOW
                # Document workflow
                from .document_service import DocumentService
                doc_service = DocumentService(self.processor, self.storage_client)
                result = await doc_service.document_workflow(file_content, filename)
                
                response_data = {
                    "workflow_id": workflow_id,
                    "workflow_type": workflow_type.value,
                    "document_id": result["document_id"],
                    "processing_result": result["processing_result"].dict(),
                    "storage_location": result["storage_location"],
                    "access_url": result["access_url"],
                    "forwarded": False
                }
            
            # Forward to webhook if provided
            if webhook_url:
                success = await self._forward_to_webhook(webhook_url, response_data)
                response_data["forwarded"] = success
            
            # Update workflow status
            self.active_workflows[workflow_id] = WorkflowStatus.COMPLETED
            
            return response_data
            
        except Exception as e:
            self.active_workflows[workflow_id] = WorkflowStatus.FAILED
            raise e
    
    async def export_result(
        self, 
        result_id: str, 
        export_format: ExportFormat
    ) -> Tuple[str, str, str]:
        """Export results in different formats"""
        
        # Get result data (from storage or cache)
        result_data = await self._get_result_data(result_id)
        
        if not result_data:
            raise ValueError(f"Result {result_id} not found")
        
        if export_format == ExportFormat.CSV:
            content = self._dict_to_csv(result_data)
            media_type = "text/csv"
            filename = f"extract_{result_id}.csv"
            
        elif export_format == ExportFormat.XML:
            content = self._dict_to_xml(result_data, "document")
            media_type = "application/xml"
            filename = f"extract_{result_id}.xml"
            
        else:  # JSON
            content = json.dumps(result_data, indent=2)
            media_type = "application/json"
            filename = f"extract_{result_id}.json"
        
        return content, media_type, filename
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        
        status = self.active_workflows.get(workflow_id)
        if not status:
            return None
        
        return {
            "workflow_id": workflow_id,
            "status": status.value,
            "last_updated": "2025-01-01T00:00:00Z"  # Would be actual timestamp
        }
    
    def get_available_workflow_types(self) -> List[Dict[str, str]]:
        """Get available workflow types"""
        
        return [
            {
                "type": WorkflowType.QUICK_SCAN.value,
                "description": "Upload → Process → Remove (temporary processing)"
            },
            {
                "type": WorkflowType.DOCUMENT_WORKFLOW.value,
                "description": "Upload → Process → Store (persistent storage)"
            }
        ]
    
    async def configure_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Configure workflow settings"""
        
        config_id = str(uuid.uuid4())
        
        # Store configuration (in production, this would go to database)
        await self.storage_client.store_workflow_config(config_id, workflow_config)
        
        return config_id
    
    async def _get_result_data(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get result data by ID"""
        
        # This is a placeholder - in production, fetch from database/storage
        return {
            "document_id": result_id,
            "vendor_name": "Boots UK",
            "total_amount": "£2.50",
            "invoice_date": "16/07/2025",
            "document_type": "receipt"
        }
    
    async def _forward_to_webhook(self, webhook_url: str, data: Dict[str, Any]) -> bool:
        """Forward data to webhook"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return False
    
    def _dict_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to CSV"""
        import io
        import csv
        
        output = io.StringIO()
        fieldnames = data.keys()
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)
        
        return output.getvalue()
    
    def _dict_to_xml(self, data: Dict[str, Any], root_tag: str = "root") -> str:
        """Convert dictionary to XML"""
        
        def dict_to_xml_recursive(d, tag):
            xml_str = f"<{tag}>"
            for key, value in d.items():
                if isinstance(value, dict):
                    xml_str += dict_to_xml_recursive(value, key)
                elif isinstance(value, list):
                    for item in value:
                        xml_str += f"<{key}>{item}</{key}>"
                else:
                    xml_str += f"<{key}>{value}</{key}>"
            xml_str += f"</{tag}>"
            return xml_str
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{dict_to_xml_recursive(data, root_tag)}'