# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI settings (fallback method)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
    
    # Ollama settings (primary method)
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    # Hugging Face settings (secondary method)
    HF_MODEL = os.getenv("HF_MODEL", "microsoft/DialoGPT-small")
    
    # General settings
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    
    # App settings
    APP_TITLE = os.getenv("APP_TITLE", "Document AI Demo")
    APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "Upload and process documents with AI")