# backend/src/middlewares/__init__.py
"""
Middleware package
"""

from .cors_middlewares import setup_cors_middleware
from .auth_middlewares import setup_auth_middleware  

__all__ = [
    "setup_cors_middleware",
    "setup_auth_middleware", 
]