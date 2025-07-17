# Document AI/IDP - PoC

🚀 **Upload documents, extract structured data with AI**

**Features**: PDF/image OCR • Smart classification • Local AI processing • Auto-fallback (Ollama → HuggingFace → OpenAI)

```
document-ai/
├── src/
│   └── document_ai/           # Your main package
│       ├── __init__.py        # Makes it a package
│       ├── app.py            # FastAPI app
│       ├── config.py         # Configuration  
│       ├── processor.py      # Document processor
│       └── utils.py          # Utilities
├── templates/                 # HTML templates (outside src)
├── static/                    # CSS/JS (outside src)  
├── uploads/                   # File uploads (outside src)
├── tests/                     # Tests (outside src)
├── pyproject.toml            # Modern config
└── README.md
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

### 3. Run
```bash
uvicorn snap_ai.app:app --reload --host 0.0.0.0 --port 8000
uvicorn app:app --reload --host 0.0.0.0 --port 8000 # or python3 app.py && open http://localhost:8000
# Visit http://localhost:8000
```

## How It Works

1. **Upload** document (PDF/TXT/image)
2. **Extract** text with OCR
3. **Classify** document type (invoice/contract/form)
4. **Extract** structured data with AI
5. **Display** results with confidence scoring

## Sample Output
```json
{
  "document_type": "invoice",
  "confidence_level": "high", 
  "extracted_data": {
    "vendor_name": "ABC Corp",
    "invoice_number": "INV-001",
    "total_amount": 1250.00
  }
}
```

## Configuration (Optional)
```bash
# .env file
OLLAMA_MODEL=llama2
OPENAI_API_KEY=your-key  # Optional fallback
```

## AI Fallback Chain
🦙 **Ollama** (local) → 🤗 **HuggingFace** (local) → 🤖 **OpenAI** (API)

*System automatically uses the best available method.*