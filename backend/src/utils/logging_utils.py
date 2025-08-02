# backend/src/utils/logging_utils.py
"""
Logging middleware configuration - Class-based logger
"""

import time
import logging
from typing import Optional
from fastapi import FastAPI, Request

class Logger:
    """
        Application logger with middleware functionality

        from ..middlewares.logging_utils import logger

        # In services:
        logger.log_processing_start("document.pdf", "invoice")
        logger.log_processing_complete("document.pdf", 1.23, 0.85)

        # In controllers:
        logger.info("Document processed successfully", request_log=False)
        logger.error("Failed to process document", request_log=False)

        # In workflows:
        logger.log_workflow_start("uuid-123", "quick_scan")
        logger.log_workflow_complete("uuid-123", "completed")
    """
    
    def __init__(self, name: str = "snap_ai"):
        self.logger = logging.getLogger(f"{name}.requests")
        self.app_logger = logging.getLogger(f"{name}.app")
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Add handler to loggers
        self.logger.addHandler(console_handler)
        self.app_logger.addHandler(console_handler)
        
        # Set levels
        self.logger.setLevel(logging.INFO)
        self.app_logger.setLevel(logging.INFO)
    
    def setup_middleware(self, app: FastAPI):
        """Setup request logging middleware"""
        
        @app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            """Log request details and timing"""
            
            start_time = time.time()
            
            # Log request
            self.info(
                f"📥 {request.method} {request.url.path} - "
                f"Client: {request.client.host if request.client else 'unknown'}"
            )
            
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            self.info(
                f"📤 {status_emoji} {response.status_code} - "
                f"{request.method} {request.url.path} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        self.app_logger.info("✅ Logging middleware configured")
    
    # Logging methods that can be used throughout the app
    def info(self, message: str, request_log: bool = True):
        """Log info message"""
        if request_log:
            self.logger.info(message)
        else:
            self.app_logger.info(message)
    
    def warning(self, message: str, request_log: bool = False):
        """Log warning message"""
        if request_log:
            self.logger.warning(message)
        else:
            self.app_logger.warning(message)
    
    def error(self, message: str, request_log: bool = False):
        """Log error message"""
        if request_log:
            self.logger.error(message)
        else:
            self.app_logger.error(message)
    
    def debug(self, message: str, request_log: bool = False):
        """Log debug message"""
        if request_log:
            self.logger.debug(message)
        else:
            self.app_logger.debug(message)
    
    def critical(self, message: str, request_log: bool = False):
        """Log critical message"""
        if request_log:
            self.logger.critical(message)
        else:
            self.app_logger.critical(message)
    
    def log_service_startup(self, service_name: str, details: Optional[str] = None):
        """Log service startup"""
        message = f"✅ {service_name} initialized"
        if details:
            message += f" - {details}"
        self.app_logger.info(message)
    
    def log_service_error(self, service_name: str, error: str):
        """Log service error"""
        self.app_logger.error(f"❌ {service_name} error: {error}")
    
    def log_processing_start(self, filename: str, doc_type: str = "document"):
        """Log document processing start"""
        self.app_logger.info(f"🔄 Processing {doc_type}: {filename}")
    
    def log_processing_complete(self, filename: str, time_taken: float, confidence: float):
        """Log document processing completion"""
        self.app_logger.info(
            f"✅ Processed: {filename} - "
            f"Time: {time_taken:.2f}s - "
            f"Confidence: {confidence:.2f}"
        )
    
    def log_workflow_start(self, workflow_id: str, workflow_type: str):
        """Log workflow start"""
        self.app_logger.info(f"🚀 Workflow started: {workflow_type} ({workflow_id})")
    
    def log_workflow_complete(self, workflow_id: str, status: str):
        """Log workflow completion"""
        emoji = "✅" if status == "completed" else "❌"
        self.app_logger.info(f"{emoji} Workflow {status}: {workflow_id}")

# Create global logger instance
logger = Logger()

# Legacy function for backward compatibility
# def setup_logging_middleware(app: FastAPI):
#     """Setup request logging middleware - Legacy function"""
#     logger.setup_middleware(app)

