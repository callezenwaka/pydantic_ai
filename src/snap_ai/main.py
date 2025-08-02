# src/snap_ai/main.py
"""
Main FastAPI application - Entry point
"""

import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .config import Config
from .dependencies import initialize_services, cleanup_services
from .routes import web, api, workflow

# Create necessary directories
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    try:
        initialize_services()
        print("✅ Application startup completed")
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        raise e
    
    yield
    
    # Shutdown
    cleanup_services()
    print("✅ Application shutdown completed")

# Initialize configuration
config = Config()

# Create FastAPI application
app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan
)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(web.router, tags=["Web UI"])
app.include_router(api.router, tags=["API"])
app.include_router(workflow.router, tags=["Workflow"])

# Root endpoint
@app.get("/ping")
async def ping():
    """Simple health check"""
    return {"message": "Snap AI is running!", "status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "src.snap_ai.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )