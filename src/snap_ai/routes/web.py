# src/snap_ai/routes/web.py
"""
Web UI routes for document processing interface
"""

import json
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from ..dependencies import get_document_service
from ..services.document_service import DocumentProcessingService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Main upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """Handle file upload and process document"""
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process document
        result = await document_service.process_single_document(
            file_content, 
            file.filename
        )
        
        # Render results page
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": result.dict(),
            "extracted_data_json": json.dumps(result.extracted_data, indent=2)
        })
        
    except Exception as e:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": str(e)
        })