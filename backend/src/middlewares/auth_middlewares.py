# backend/src/middlewares/auth_middlewares.py
"""
Authentication middleware configuration
"""

import time
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config.app_config import Config

security = HTTPBearer(auto_error=False)

def setup_auth_middleware(app: FastAPI):
    """Setup authentication middleware"""
    
    config = Config()
    
    # Skip auth for development if configured
    if getattr(config, 'SKIP_AUTH', False):
        print("⚠️ Authentication middleware skipped (development mode)")
        return
    
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        """Authentication middleware"""
        
        # Skip auth for certain paths
        skip_paths = [
            "/ping",
            "/info", 
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/"  # Web interface for backward compatibility
        ]
        
        # Check if path should skip auth
        if any(request.url.path.startswith(path) for path in skip_paths):
            response = await call_next(request)
            return response
        
        # For API endpoints, check for API key or token
        if request.url.path.startswith("/api"):
            api_key = request.headers.get("X-API-Key")
            authorization = request.headers.get("Authorization")
            
            # Simple API key check (implement proper auth as needed)
            if not api_key and not authorization:
                # For now, allow requests without auth in development
                # In production, you'd raise HTTPException(401, "Authentication required")
                pass
        
        response = await call_next(request)
        return response
    
    print("✅ Authentication middleware configured")