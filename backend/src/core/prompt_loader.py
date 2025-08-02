# prompt_loader.py
"""
Utility for loading document processing prompts from YAML files
"""

import yaml
from pathlib import Path
from typing import Dict, Any

class PromptLoader:
    """Load and manage document processing prompts"""
    
    def __init__(self, prompts_file: str = "prompts.yaml"):
        self.prompts_file = Path(prompts_file)
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from YAML file"""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"⚠️ Prompts file {self.prompts_file} not found. Using default prompts.")
            return self._get_default_prompts()
        except yaml.YAMLError as e:
            print(f"⚠️ Error loading prompts: {e}. Using default prompts.")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """Fallback prompts if file loading fails"""
        return {
            "document_types": {
                "invoice": {
                    "ollama": "Extract invoice information from: {text}\nReturn JSON:",
                    "openai": "Extract invoice information from: {text}\nReturn JSON:",
                    "huggingface": "Extract invoice from: {text_preview}...\nJSON:"
                }
            },
            "default": {
                "ollama": "Extract information from: {text}\nReturn JSON:",
                "openai": "Extract information from: {text}\nReturn JSON:",
                "huggingface": "Extract from: {text_preview}...\nJSON:"
            }
        }
    
    def get_prompt(self, doc_type: str, method: str) -> str:
        """Get prompt for specific document type and extraction method"""
        
        # Try to get document-specific prompt
        if doc_type in self.prompts.get("document_types", {}):
            doc_prompts = self.prompts["document_types"][doc_type]
            if method in doc_prompts:
                return doc_prompts[method]
        
        # Fallback to default prompt
        default_prompts = self.prompts.get("default", {})
        if method in default_prompts:
            return default_prompts[method]
        
        # Ultimate fallback
        return f"Extract {doc_type} information from: {{text}}\nReturn JSON:"
    
    def format_prompt(self, doc_type: str, method: str, text: str) -> str:
        """Get formatted prompt ready for AI model"""
        prompt_template = self.get_prompt(doc_type, method)
        
        # Prepare variables for formatting
        format_vars = {
            "text": text,
            "text_preview": text[:300] if len(text) > 300 else text
        }
        
        try:
            return prompt_template.format(**format_vars)
        except KeyError as e:
            print(f"⚠️ Missing variable in prompt template: {e}")
            # Return prompt with text only
            return prompt_template.replace("{text}", text).replace("{text_preview}", text[:300])
    
    def reload_prompts(self):
        """Reload prompts from file (useful for development)"""
        self.prompts = self._load_prompts()
        print("✅ Prompts reloaded")
    
    def get_available_document_types(self) -> list:
        """Get list of available document types"""
        return list(self.prompts.get("document_types", {}).keys())
    
    def get_available_methods(self) -> list:
        """Get list of available extraction methods"""
        methods = set()
        
        # Collect methods from document types
        for doc_type in self.prompts.get("document_types", {}).values():
            methods.update(doc_type.keys())
        
        # Add methods from default
        methods.update(self.prompts.get("default", {}).keys())
        
        return list(methods)