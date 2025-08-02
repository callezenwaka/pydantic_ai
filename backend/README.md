# Document AI/IDP - MVC Edition

🚀 **Upload documents, extract structured data with AI** • **Two workflows: Quick Scan & Document Workflow**

**Features**: PDF/image OCR • Smart classification • Local AI processing • Auto-fallback (Ollama → HuggingFace → OpenAI) • Mobile API • Storage integration

## Workflows

📱 **Quick Scan**: Upload → Process → Remove (temporary processing)  
💾 **Document Workflow**: Upload → Process → Store (persistent storage)

## Architecture

```
src/
├── controllers/          # HTTP request/response logic
├── services/            # Business logic
├── routes/              # URL endpoints  
├── models/              # Data models
├── schemas/             # API validation
├── core/                # Processor, storage, utilities
├── dependencies/        # Dependency injection
├── middlewares/         # CORS, auth, logging
├── config/              # Configuration
└── main.py              # FastAPI app entry point
```

## Quick Start

### 1. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama2
```

### 2. Install Dependencies
```bash
pip install -e .
```

### 3. Run Application
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: **http://localhost:8000**

## API Endpoints

### **Documents**
```bash
# Quick Scan (temporary)
POST /api/documents/scan

# Document Workflow (persistent) 
POST /api/documents/workflow

# List stored documents
GET /api/documents

# Batch processing
POST /api/documents/batch-scan
POST /api/documents/batch-workflow
```

### **Workflows** 
```bash
# Export results
GET /api/workflow/export/{result_id}?format=json|csv|xml

# Webhook integration
POST /api/workflow/webhook

# System info
GET /api/health
GET /api/workflow/types
```

### **Web Interface** (Backward Compatible)
```bash
GET /              # Upload page
POST /upload       # Process document (quick scan)
```

## Mobile & Frontend Support

**Mobile Apps**: All `/api/*` endpoints  
**Future Vue/React**: All `/api/*` endpoints  
**Current Web**: `/` and `/upload` (Jinja templates)

### Mobile Testing
```bash
# Find your IP
ipconfig getifaddr en0  # Mac
ip route get 1 | awk '{print $7}' # Linux

# Access from mobile: http://YOUR_IP:8000/api/documents/scan
```

## Sample API Response
```json
{
  "document_type": "invoice",
  "confidence_level": "high",
  "ml_confidence": 0.92,
  "needs_human_review": false,
  "extracted_data": {
    "vendor_name": "ABC Corp",
    "invoice_number": "INV-001", 
    "total_amount": "$1,250.00",
    "invoice_date": "2024-01-15"
  },
  "processing_time": "1.23s",
  "extraction_method": "ollama"
}
```

## Document Workflow Response
```json
{
  "document_id": "uuid-123",
  "processing_result": { /* same as above */ },
  "storage_location": "gs://bucket/documents/uuid-123/file.pdf",
  "access_url": "https://storage.googleapis.com/signed-url"
}
```

## Configuration
```bash
# .env file
OLLAMA_MODEL=llama2
HUGGINGFACE_MODEL=microsoft/DialoGPT-small
OPENAI_API_KEY=your-key  # Optional fallback
GOOGLE_CLOUD_BUCKET=your-bucket  # For document workflow
```

## AI Fallback Chain
🦙 **Ollama** (local) → 🤗 **HuggingFace** (local) → 🤖 **OpenAI** (API)

## How It Works

**Quick Scan**: Upload → OCR → AI Processing → JSON Response → File Deleted  
**Document Workflow**: Upload → OCR → AI Processing → Store to Cloud → Return Access URL

*Perfect for both rapid testing and production document management.*