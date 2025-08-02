# src/snap_ai/routes/api.py
"""
API routes for document processing
"""

from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse

from ..dependencies import get_document_service
from ..services.document_service import DocumentProcessingService
from ..models.document import ProcessingResult, BatchProcessingResult, ProcessingRequest

router = APIRouter(prefix="/api", tags=["Document Processing"])

@router.post("/process", response_model=ProcessingResult)
async def process_document(
    file: UploadFile = File(...),
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """Process a single document via API"""
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process document
        result = await document_service.process_single_document(
            file_content, 
            file.filename
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-process", response_model=BatchProcessingResult)
async def batch_process(
    files: List[UploadFile] = File(...),
    webhook_url: str = Form(None),
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """Process multiple documents in batch"""
    
    try:
        # Prepare files data
        files_data = []
        for file in files:
            content = await file.read()
            files_data.append((content, file.filename))
        
        # Process batch
        result = await document_service.process_batch_documents(files_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """Health check endpoint"""
    
    try:
        # Check if processor is ready
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