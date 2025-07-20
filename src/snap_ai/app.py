# app.py
"""
FastAPI Web Application with File Upload for Document AI
"""

import json
import uuid
import uvicorn
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from src.snap_ai.processor import Processor
from src.snap_ai.config import Config
from src.snap_ai.utils import extract_text_from_file

# Create directories
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True) 
Path("uploads").mkdir(exist_ok=True)

# Global processor instance
processor: Optional[Processor] = None

config = Config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    global processor
    try:
        processor = Processor()
        print("✅ Document AI processor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        print("💡 Make sure OPENAI_API_KEY is set in environment")
    
    yield
    
    # Shutdown (cleanup if needed)
    print("🔄 Shutting down Document AI processor...")

# Initialize FastAPI with lifespan
app = FastAPI(
    title=config.APP_TITLE, 
    description=config.APP_DESCRIPTION,
    lifespan=lifespan
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Main upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    if not processor:
        raise HTTPException(status_code=500, detail="Processor not initialized")
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Handle camera captures (they come as captured_image.jpg)
        is_camera_capture = file.filename.startswith('captured_image')
        
        # Check file type
        allowed_types = ['.txt', '.pdf', '.png', '.jpg', '.jpeg']
        file_ext = Path(file.filename).suffix.lower()
        
        # For camera captures, ensure it's treated as jpeg
        if is_camera_capture and not file_ext:
            file_ext = '.jpg'
            
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not supported. Use: {', '.join(allowed_types)}"
            )
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = Path("uploads") / filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract text from file
        text = extract_text_from_file(file_path, file_ext)
        
        # Process document
        result = processor.process_document(text)
        
        # Add file info to result
        result["uploaded_file"] = file.filename
        result["file_size"] = len(content)
        result["file_type"] = file_ext
        
        # Clean up uploaded file
        file_path.unlink(missing_ok=True)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": result,
            "extracted_data_json": json.dumps(result["extracted_data"], indent=2)
        })
        
    except Exception as e:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": str(e)
        })

@app.post("/api/process")
async def api_process_document(file: UploadFile = File(...)):
    """API endpoint for document processing"""
    
    if not processor:
        raise HTTPException(status_code=500, detail="Processor not initialized")
    
    try:
        # Extract text
        content = await file.read()
        file_ext = Path(file.filename).suffix.lower()
        
        # Save temporarily
        temp_path = Path("uploads") / f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        text = extract_text_from_file(temp_path, file_ext)
        
        # Process
        result = processor.process_document(text)
        
        # Clean up
        temp_path.unlink(missing_ok=True)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if processor else "unhealthy",
        "processor_ready": processor is not None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)