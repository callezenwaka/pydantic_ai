# src/snap_ai/core/service_manager.py
"""
Service lifecycle management - Global service instances and initialization
"""

from typing import Optional
from fastapi import HTTPException

from .processor import Processor
from .storage import StorageClient

# Global instances
_processor: Optional[Processor] = None
_storage_client: Optional[StorageClient] = None

def initialize_services():
    """Initialize all services on startup"""
    global _processor, _storage_client
    
    try:
        # Initialize core services
        _processor = Processor()
        _storage_client = StorageClient()
        
        print("✅ All services initialized")
        print(f"   📊 Processor: {_processor.extraction_method}")
        print(f"   💾 Storage: {_storage_client.bucket_name}")
        
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        raise e

def cleanup_services():
    """Cleanup services on shutdown"""
    global _processor, _storage_client
    
    print("🔄 Shutting down services...")
    
    # Cleanup processor if needed
    _processor = None
    
    # Cleanup storage client if needed  
    _storage_client = None
    
    print("✅ Services cleaned up")

def get_processor() -> Processor:
    """Get processor instance"""
    if _processor is None:
        raise HTTPException(status_code=503, detail="Processor not initialized")
    return _processor

def get_storage_client() -> StorageClient:
    """Get storage client instance"""
    if _storage_client is None:
        raise HTTPException(status_code=503, detail="Storage client not initialized")
    return _storage_client

def is_healthy() -> bool:
    """Check if all services are healthy"""
    return _processor is not None and _storage_client is not None
