# backend/src/main.py
"""
Main FastAPI application - Entry point
"""

import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from src.utils.logging_utils import logger
from src.config.app_config import Config
from src.core.service_manager import initialize_services, cleanup_services

from .routes.document_routes import router as document_router
from .routes.workflow_routes import router as workflow_router

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
        logger.info("✅ Application startup completed")
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
    version=config.APP_VERSION,
    lifespan=lifespan
)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(
    document_router,
    tags=["Documents"]
)

app.include_router(
    workflow_router, 
    tags=["Workflows"]
)
# app.include_router(bookRouter, prefix=f"/api/{Config.api_version}/books", tags=["books"])

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