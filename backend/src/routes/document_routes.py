# src/snap_ai/routes/document_routes.py
"""
Document routes - URL endpoint definitions
"""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Query
from fastapi.responses import HTMLResponse

from ..controllers.document_controller import DocumentController
from ..dependencies.document_dependencies import get_document_service
from ..models.document_model import ProcessingResult, BatchProcessingResult

router = APIRouter()
controller = DocumentController()

# Web Interface Routes (Backward Compatibility)
@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Main upload page"""
    return await controller.upload_page_web(request)

@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    document_service = Depends(get_document_service)
):
    """Handle file upload (quick scan only)"""
    return await controller.upload_file_web(request, file, document_service)

# API Routes
@router.post("/api/documents/scan", response_model=ProcessingResult)
async def quick_scan(
    file: UploadFile = File(...),
    document_service = Depends(get_document_service)
):
    """Quick scan: upload → process → remove"""
    return await controller.quick_scan_api(file, document_service)

@router.post("/api/documents/workflow")
async def document_workflow(
    file: UploadFile = File(...),
    document_service = Depends(get_document_service)
):
    """Document workflow: upload → process → store"""
    return await controller.document_workflow_api(file, document_service)

@router.post("/api/documents/batch-scan", response_model=BatchProcessingResult)
async def batch_scan(
    files: List[UploadFile] = File(...),
    document_service = Depends(get_document_service)
):
    """Batch quick scan"""
    return await controller.batch_scan_api(files, document_service)

@router.post("/api/documents/batch-workflow")
async def batch_workflow(
    files: List[UploadFile] = File(...),
    document_service = Depends(get_document_service)
):
    """Batch document workflow"""
    return await controller.batch_workflow_api(files, document_service)

@router.get("/api/documents")
async def list_documents(
    limit: int = Query(default=100, le=1000),
    skip: int = Query(default=0, ge=0),
    document_service = Depends(get_document_service)
):
    """List stored documents"""
    return await controller.list_documents_api(limit, skip, document_service)

@router.get("/api/documents/{doc_id}")
async def get_document(
    doc_id: str,
    document_service = Depends(get_document_service)
):
    """Get specific document"""
    return await controller.get_document_api(doc_id, document_service)

@router.delete("/api/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    document_service = Depends(get_document_service)
):
    """Delete document"""
    return await controller.delete_document_api(doc_id, document_service)

@router.get("/api/health")
async def health_check(
    document_service = Depends(get_document_service)
):
    """System health check"""
    return await controller.health_check_api(document_service)