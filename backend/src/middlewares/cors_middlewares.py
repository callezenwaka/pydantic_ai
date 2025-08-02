# backend/src/middlewares/cors_middlewares.py
"""
CORS middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.app_config import Config

def setup_cors_middleware(app: FastAPI):
    """Setup CORS middleware for frontend integration"""
    config = Config()

    # Get allowed origins from config or use defaults
    allowed_origins = getattr(config, 'ALLOWED_ORIGINS', [
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ])
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
        ],
        expose_headers=["Content-Disposition"],  # For file downloads
    )
    
    print("✅ CORS middleware configured")
