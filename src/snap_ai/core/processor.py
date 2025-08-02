# src/snap_ai/core/processor.py
"""
Minimal Document AI/IDP System - Proof of Concept
Combines OCR + Traditional ML + Local AI for document understanding
"""

import json
import time
import requests
from typing import Dict, Any, Tuple
from enum import Enum

from src.snap_ai.prompt_loader import PromptLoader
from src.snap_ai.config import Config
from ..models.document import DocumentType, ConfidenceLevel, ExtractionMethod

# Traditional ML
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Keep LangChain as optional fallback
try:
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class Processor:
    """Main Document AI processor combining traditional ML + Local AI"""

    def __init__(self):
        self.config = Config()

        # Initialize prompt loader
        self.prompt_loader = PromptLoader("prompts.yaml")
        print(f"✅ Loaded prompts for document types: {self.prompt_loader.get_available_document_types()}")
        

        # Initialize traditional ML classifier
        self.classifier = self._setup_classifier()

        # Try to initialize AI extractors in order of preference
        self.extraction_method = "none"

        # 1. Try Ollama first
        if self._init_ollama():
            self.extraction_method = "ollama"
            print("🦙 Using Ollama for extraction")

        # 2. Try Hugging Face if Ollama fails
        elif self._init_huggingface():
            self.extraction_method = "huggingface"
            print("🤗 Using Hugging Face for extraction")

        # 3. Try OpenAI if both fail
        elif self._init_openai():
            self.extraction_method = "openai"
            print("🤖 Using OpenAI for extraction")

        else:
            raise RuntimeError("❌ No AI extraction method available!")

        print("✅ Document AI processor initialized")

    def _init_ollama(self) -> bool:
        """Try to initialize Ollama"""
        try:
            self.ollama_url = getattr(
                self.config, "OLLAMA_URL", "http://localhost:11434"
            )
            self.ollama_model = getattr(self.config, "OLLAMA_MODEL", "llama2")

            # Test connection
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _init_huggingface(self) -> bool:
        """Try to initialize Hugging Face"""
        try:
            from transformers import pipeline

            self.hf_generator = pipeline(
                "text-generation",
                model=getattr(self.config, "HF_MODEL", "microsoft/DialoGPT-small"),
                max_length=256,
                do_sample=True,
                temperature=0.7,
                pad_token_id=50256,
            )
            return True
        except:
            return False

    def _init_openai(self) -> bool:
        """Try to initialize OpenAI (your original code)"""
        try:
            if (
                LANGCHAIN_AVAILABLE
                and hasattr(self.config, "OPENAI_API_KEY")
                and self.config.OPENAI_API_KEY
            ):
                self.llm = OpenAI(
                    openai_api_key=self.config.OPENAI_API_KEY,
                    model_name=self.config.MODEL_NAME,
                    temperature=0.0,
                )
                return True
        except:
            pass
        return False

    def _setup_classifier(self) -> Pipeline:
        """Setup traditional ML classifier"""

        # Enhanced training data with receipts
        training_texts = [
            # Invoices
            "Invoice Number INV-001 Total Amount $1500 Due Date 2024-01-15",
            "INVOICE Company ABC Total: $2300 Date: Jan 15 2024",
            "Bill Invoice #12345 Amount Due: $890 Payment Terms: Net 30",
            
            # Contracts  
            "This Agreement between Party A and Party B effective January 1 2024",
            "CONTRACT for services Term: 12 months Payment: Monthly",
            "Service Agreement Party obligations Terms and conditions",
            
            # Forms
            "Application Form Name: John Doe Address: 123 Main St Phone: 555-0123",
            "Registration Form Personal Information Company Department",
            "FORM Submit application Date of birth Emergency contact",
            
            # Receipts
            "Receipt Boots UK Total £2.50 Card Payment Thank you for shopping",
            "RECEIPT Tesco Store 1234 Total: $15.67 Cash Paid",
            "Thank you for your purchase Receipt Total Amount £25.00 Change £5.00",
        ]

        training_labels = [
            "invoice", "invoice", "invoice",     # Invoices
            "contract", "contract", "contract",  # Contracts  
            "form", "form", "form",             # Forms
            "receipt", "receipt", "receipt",     # Receipts
        ]

        # Create and train classifier
        classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(max_features=1000, stop_words="english")),
                ("nb", MultinomialNB()),
            ]
        )

        classifier.fit(training_texts, training_labels)
        print("✅ Traditional ML classifier trained")

        return classifier

    def process_document(self, text: str) -> Dict[str, Any]:
        """
        Main processing pipeline

        Args:
            text: Document text (from OCR)

        Returns:
            Complete processing results
        """
        start_time = time.time()

        print(f"\n🔄 Processing document...")
        print(f"📄 Text preview: {text[:100]}...")

        # Step 1: Traditional ML Classification
        doc_type, ml_confidence = self._classify_document(text)
        print(f"📊 Classification: {doc_type} (confidence: {ml_confidence:.2f})")

        # Step 2: AI Extraction (updated to use different methods)
        if self.extraction_method == "ollama":
            extracted_data = self._extract_with_ollama(text, doc_type)
        elif self.extraction_method == "huggingface":
            extracted_data = self._extract_with_huggingface(text, doc_type)
        elif self.extraction_method == "openai":
            extracted_data = self._extract_with_gpt4(text, doc_type)
        else:
            extracted_data = {"error": "No extraction method available"}

        print(f"🤖 {self.extraction_method.title()} extraction completed")

        # Step 2.5: Post-process extracted data
        extracted_data = self._post_process_extracted_data(extracted_data)

        # Step 3: Calculate overall confidence
        overall_confidence = self._calculate_confidence(ml_confidence, extracted_data)
        confidence_level = self._get_confidence_level(overall_confidence)

        # Step 4: Determine if human review needed
        needs_review = confidence_level == ConfidenceLevel.LOW

        processing_time = time.time() - start_time

        # Get the actual model name being used
        model_display_name = self._get_model_display_name()
        
        result = {
            "document_type": doc_type,
            "ml_confidence": ml_confidence,
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level.value,
            "needs_human_review": needs_review,
            "extracted_data": extracted_data,
            "processing_time": f"{processing_time:.2f}s",
            "extraction_method": self.extraction_method,
            "model_display_name": model_display_name,
            "raw_text": text,
        }

        print(f"✅ Processing completed in {processing_time:.2f}s")
        return result

    def _classify_document(self, text: str) -> Tuple[str, float]:
        """Traditional ML classification"""

        # Get prediction and probabilities
        prediction = self.classifier.predict([text])[0]
        probabilities = self.classifier.predict_proba([text])[0]
        confidence = max(probabilities)

        return prediction, confidence

    def _extract_with_ollama(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Extract using Ollama with centralized prompts"""

        # Get formatted prompt from prompt loader
        prompt = self.prompt_loader.format_prompt(doc_type, "ollama", text)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "top_p": 0.9},
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return self._parse_json_response(result.get("response", ""))
            else:
                return {"error": f"Ollama API error: {response.status_code}"}

        except Exception as e:
            return {"error": str(e), "raw_response": ""}

    def _extract_with_huggingface(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Extract using Hugging Face with centralized prompts"""

        # Get formatted prompt from prompt loader
        prompt = self.prompt_loader.format_prompt(doc_type, "huggingface", text)

        try:
            result = self.hf_generator(
                prompt, max_length=200, num_return_sequences=1, truncation=True
            )

            response = result[0]["generated_text"]
            return self._parse_json_response(response)

        except Exception as e:
            return {"error": str(e), "raw_response": ""}

    def _extract_with_gpt4(self, text: str, doc_type: str) -> Dict[str, Any]:
        """GPT-4 intelligent extraction using LangChain with centralized prompts"""

        # Get prompt template from prompt loader
        prompt_template_str = self.prompt_loader.get_prompt(doc_type, "openai")

        # Create LangChain prompt and chain
        prompt = PromptTemplate(template=prompt_template_str, input_variables=["text"])
        chain = LLMChain(llm=self.llm, prompt=prompt)

        try:
            # Run extraction
            response = chain.run(text=text)

            # Parse JSON from response
            return self._parse_json_response(response)

        except Exception as e:
            print(f"⚠️ GPT-4 extraction error: {e}")
            return {"error": str(e), "raw_response": ""}

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response"""
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1

            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"raw_response": response}

        except json.JSONDecodeError:
            return {"raw_response": response}

    def _calculate_confidence(
        self, ml_confidence: float, extracted_data: Dict
    ) -> float:
        """Calculate overall confidence score"""

        # Data completeness factor
        data_completeness = 0.5  # Default
        if extracted_data and "error" not in extracted_data:
            non_empty_fields = sum(1 for v in extracted_data.values() if v)
            total_fields = len(extracted_data)
            data_completeness = (
                non_empty_fields / total_fields if total_fields > 0 else 0.5
            )

        # Weighted average
        overall_confidence = (ml_confidence * 0.4) + (data_completeness * 0.6)

        return min(1.0, max(0.0, overall_confidence))

    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert confidence score to level"""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= self.config.CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _get_model_display_name(self) -> str:
        """Get display name for the AI model being used"""
        if self.extraction_method == "ollama":
            # Handle different Ollama models
            model_mapping = {
                "llama2": "Llama 2",
                "mistral": "Mistral", 
                "codellama": "Code Llama",
                "llama3": "Llama 3"
            }
            return model_mapping.get(self.ollama_model, self.ollama_model.title())
            
        elif self.extraction_method == "huggingface":
            # Handle different HF models
            model_name = self.config.HF_MODEL.split('/')[-1]
            model_mapping = {
                "DialoGPT-small": "DialoGPT Small",
                "DialoGPT-medium": "DialoGPT Medium",
                "distilbert-base-uncased": "DistilBERT"
            }
            return model_mapping.get(model_name, model_name)
            
        elif self.extraction_method == "openai":
            # Handle different OpenAI models
            model_mapping = {
                "gpt-4": "GPT-4",
                "gpt-3.5-turbo": "GPT-3.5 Turbo",
                "gpt-4-turbo": "GPT-4 Turbo"
            }
            return model_mapping.get(self.config.MODEL_NAME, self.config.MODEL_NAME)
            
        else:
            return "Unknown Model"
        
    def _post_process_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process extracted data to format complex fields better"""
        
        # Fields that might contain item lists
        item_fields = ['items_purchased', 'line_items', 'items', 'products']
        
        for field in item_fields:
            if field in extracted_data:
                raw_value = extracted_data[field]
                
                # Try to parse JSON string to structured data
                if isinstance(raw_value, str):
                    try:
                        import json
                        import re
                        
                        # Try to extract JSON array from string
                        match = re.search(r'\[.*\]', raw_value)
                        if match:
                            items_array = json.loads(match.group())
                            
                            # Convert to readable format
                            if isinstance(items_array, list) and len(items_array) > 0:
                                readable_items = []
                                for item in items_array:
                                    if isinstance(item, dict):
                                        desc = item.get('description', item.get('name', 'Item'))
                                        qty = item.get('quantity', item.get('qty', 1))
                                        price = item.get('unit_price', item.get('price', ''))
                                        total = item.get('total', item.get('amount', ''))
                                        
                                        item_str = f"{desc}"
                                        if qty and qty != 1:
                                            item_str += f" (Qty: {qty})"
                                        if price:
                                            item_str += f" @ {price}"
                                        if total:
                                            item_str += f" = {total}"
                                        
                                        readable_items.append(item_str)
                                    else:
                                        readable_items.append(str(item))
                                
                                # Store both formats
                                extracted_data[field] = "\n".join([f"• {item}" for item in readable_items])
                                extracted_data[f"{field}_raw"] = raw_value  # Keep original for API users
                                
                    except (json.JSONDecodeError, AttributeError):
                        # If parsing fails, try simple cleanup
                        if raw_value.startswith('[') and raw_value.endswith(']'):
                            # Remove brackets and quotes, split by commas
                            cleaned = raw_value.strip('[]').replace("'", "").replace('"', '')
                            items = [item.strip() for item in cleaned.split(',') if item.strip()]
                            if len(items) <= 5:  # Only if reasonable number
                                extracted_data[field] = "\n".join([f"• {item}" for item in items[:5]])
        
        return extracted_data

    def get_supported_document_types(self) -> list:
        """Get list of supported document types"""
        if hasattr(self, 'prompt_loader'):
            return self.prompt_loader.get_available_document_types()
        else:
            return ["invoice", "contract", "form", "receipt"]
    
    def get_model_display_name(self) -> str:
        """Get display name for the AI model being used"""
        if self.extraction_method == "ollama":
            model_mapping = {
                "llama2": "Llama 2",
                "mistral": "Mistral", 
                "codellama": "Code Llama",
                "llama3": "Llama 3"
            }
            return model_mapping.get(self.ollama_model, self.ollama_model.title())
            
        elif self.extraction_method == "huggingface":
            model_name = self.config.HF_MODEL.split('/')[-1]
            model_mapping = {
                "DialoGPT-small": "DialoGPT Small",
                "DialoGPT-medium": "DialoGPT Medium",
                "distilbert-base-uncased": "DistilBERT"
            }
            return model_mapping.get(model_name, model_name)
            
        elif self.extraction_method == "openai":
            model_mapping = {
                "gpt-4": "GPT-4",
                "gpt-3.5-turbo": "GPT-3.5 Turbo",
                "gpt-4-turbo": "GPT-4 Turbo"
            }
            return model_mapping.get(self.config.MODEL_NAME, self.config.MODEL_NAME)
            
        else:
            return "Unknown Model"