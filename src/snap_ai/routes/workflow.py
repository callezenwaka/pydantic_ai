# src/snap_ai/routes/workflow.py
"""
Workflow integration routes
"""

import aiohttp
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, Response

from ..dependencies import get_document_service
from ..services.document_service import DocumentProcessingService
from ..models.document import PipelineData

router = APIRouter(prefix="/api/workflow", tags=["Workflow Integration"])

@router.post("/process-and-forward")
async def process_and_forward(
    file: UploadFile = File(...),
    webhook_url: str = Form(None),
    output_format: str = Form("json"),
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """Process document and forward to webhook"""
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process document
        result = await document_service.process_single_document(
            file_content, 
            file.filename
        )
        
        # Format for pipeline
        pipeline_data = document_service.format_for_pipeline(result)
        
        # Forward to webhook if provided
        forwarded = False
        if webhook_url:
            await _forward_to_webhook(webhook_url, pipeline_data.dict())
            forwarded = True
        
        return JSONResponse(content={
            "processing_result": result.dict(),
            "pipeline_data": pipeline_data.dict(),
            "forwarded": forwarded
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{result_id}")
async def export_result(
    result_id: str, 
    format: str = "json",
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """Export processed results in different formats"""
    
    # This is a placeholder - in production, you'd fetch from database
    sample_data = {
        "document_id": result_id,
        "vendor_name": "Boots UK",
        "total_amount": "£2.50",
        "invoice_date": "16/07/2025",
        "document_type": "receipt"
    }
    
    if format == "csv":
        csv_content = _dict_to_csv(sample_data)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=extract_{result_id}.csv"}
        )
    
    elif format == "xml":
        xml_content = _dict_to_xml(sample_data, "document")
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename=extract_{result_id}.xml"}
        )
    
    else:  # json
        return JSONResponse(content=sample_data)

# Helper functions
async def _forward_to_webhook(webhook_url: str, data: dict):
    """Forward data to webhook"""
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                webhook_url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    print(f"⚠️ Webhook failed: {response.status}")
                else:
                    print("✅ Data forwarded to pipeline")
        except Exception as e:
            print(f"❌ Webhook error: {e}")

def _dict_to_csv(data: dict) -> str:
    """Convert dictionary to CSV"""
    import io
    import csv
    
    output = io.StringIO()
    fieldnames = data.keys()
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(data)
    
    return output.getvalue()

def _dict_to_xml(data: dict, root_tag: str = "root") -> str:
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
