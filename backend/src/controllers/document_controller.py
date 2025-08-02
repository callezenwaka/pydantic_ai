# backend/src/controllers/document_controller.py
"""
Document controller - Handles HTTP request/response logic
"""

import json
from typing import List
from fastapi import UploadFile, Request, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..services.document_service import DocumentService
from ..models.document_model import ProcessingResult, BatchProcessingResult


class DocumentController:
    """Controller for document processing endpoints"""
    
    def __init__(self):
        self.templates = Jinja2Templates(directory="templates")
    
    # Web Interface Methods (Backward Compatibility)
    async def upload_page_web(self, request: Request) -> HTMLResponse:
        """Render upload page"""
        return self.templates.TemplateResponse("upload.html", {"request": request})
    
    async def upload_file_web(
        self, 
        request: Request, 
        file: UploadFile, 
        document_service: DocumentService
    ) -> HTMLResponse:
        """Handle web file upload (quick scan only)"""
        try:
            file_content = await file.read()
            result = await document_service.quick_scan(file_content, file.filename)
            
            return self.templates.TemplateResponse("results.html", {
                "request": request,
                "result": result.dict(),
                "extracted_data_json": json.dumps(result.extracted_data, indent=2)
            })
            
        except Exception as e:
            return self.templates.TemplateResponse("upload.html", {
                "request": request,
                "error": str(e)
            })
    
    # API Methods
    async def quick_scan_api(
        self, 
        file: UploadFile, 
        document_service: DocumentService
    ) -> ProcessingResult:
        """API endpoint for quick document scan"""
        try:
            file_content = await file.read()
            result = await document_service.quick_scan(file_content, file.filename)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def document_workflow_api(
        self, 
        file: UploadFile, 
        document_service: DocumentService
    ) -> dict:
        """API endpoint for document workflow (store)"""
        try:
            file_content = await file.read()
            result = await document_service.document_workflow(file_content, file.filename)
            
            return {
                "document_id": result["document_id"],
                "processing_result": result["processing_result"].dict(),
                "storage_location": result["storage_location"],
                "access_url": result["access_url"]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def batch_scan_api(
        self, 
        files: List[UploadFile], 
        document_service: DocumentService
    ) -> BatchProcessingResult:
        """API endpoint for batch quick scan"""
        try:
            files_data = []
            for file in files:
                content = await file.read()
                files_data.append((content, file.filename))
            
            result = await document_service.batch_quick_scan(files_data)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def batch_workflow_api(
        self, 
        files: List[UploadFile], 
        document_service: DocumentService
    ) -> dict:
        """API endpoint for batch document workflow"""
        try:
            files_data = []
            for file in files:
                content = await file.read()
                files_data.append((content, file.filename))
            
            result = await document_service.batch_document_workflow(files_data)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def list_documents_api(
        self, 
        limit: int, 
        skip: int, 
        document_service: DocumentService
    ) -> dict:
        """API endpoint to list stored documents"""
        try:
            documents = await document_service.list_stored_documents(limit=limit, skip=skip)
            return documents
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_document_api(
        self, 
        doc_id: str, 
        document_service: DocumentService
    ) -> dict:
        """API endpoint to get specific document"""
        try:
            document = await document_service.get_stored_document(doc_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_document_api(
        self, 
        doc_id: str, 
        document_service: DocumentService
    ) -> dict:
        """API endpoint to delete document"""
        try:
            success = await document_service.delete_stored_document(doc_id)
            if not success:
                raise HTTPException(status_code=404, detail="Document not found")
            return {"message": "Document deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def health_check_api(self, document_service: DocumentService) -> dict:
        """API endpoint for health check"""
        try:
            is_healthy = document_service.processor is not None
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "processor_ready": is_healthy,
                "available_methods": document_service.processor.get_supported_document_types() if is_healthy else [],
                "available_model": document_service.processor.get_model_display_name() if is_healthy else []
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }