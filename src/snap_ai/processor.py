# processor.py
"""
Minimal Document AI/IDP System - Proof of Concept
Combines OCR + Traditional ML + Local AI for document understanding
"""

import json
import time
import requests
from typing import Dict, Any, Tuple
from enum import Enum

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

from src.snap_ai.config import Config


class DocumentType(Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    FORM = "form"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Processor:
    """Main Document AI processor combining traditional ML + Local AI"""

    def __init__(self):
        self.config = Config()

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

        # Sample training data
        training_texts = [
            "Invoice Number INV-001 Total Amount $1500 Due Date 2024-01-15",
            "INVOICE Company ABC Total: $2300 Date: Jan 15 2024",
            "Bill Invoice #12345 Amount Due: $890 Payment Terms: Net 30",
            "This Agreement between Party A and Party B effective January 1 2024",
            "CONTRACT for services Term: 12 months Payment: Monthly",
            "Service Agreement Party obligations Terms and conditions",
            "Application Form Name: John Doe Address: 123 Main St Phone: 555-0123",
            "Registration Form Personal Information Company Department",
            "FORM Submit application Date of birth Emergency contact",
        ]

        training_labels = [
            "invoice",
            "invoice",
            "invoice",
            "contract",
            "contract",
            "contract",
            "form",
            "form",
            "form",
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

        # Step 3: Calculate overall confidence
        overall_confidence = self._calculate_confidence(ml_confidence, extracted_data)
        confidence_level = self._get_confidence_level(overall_confidence)

        # Step 4: Determine if human review needed
        needs_review = confidence_level == ConfidenceLevel.LOW

        processing_time = time.time() - start_time

        result = {
            "document_type": doc_type,
            "ml_confidence": ml_confidence,
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level.value,
            "needs_human_review": needs_review,
            "extracted_data": extracted_data,
            "processing_time": f"{processing_time:.2f}s",
            "extraction_method": self.extraction_method,
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
        """Extract using Ollama"""

        prompts = {
            "invoice": f"""Extract invoice information from this text and return ONLY valid JSON:

            Text: {text}

            Extract these exact fields:
            - vendor_name: company name
            - invoice_number: invoice number  
            - total_amount: total amount (number only)
            - invoice_date: date
            - customer_info: customer details

            Return JSON format:""",
                        "contract": f"""Extract contract information from this text and return ONLY valid JSON:

            Text: {text}

            Extract these exact fields:
            - parties: list of contract parties
            - contract_type: type of contract
            - effective_date: start date
            - key_terms: important terms

            Return JSON format:""",
                        "form": f"""Extract form information from this text and return ONLY valid JSON:

            Text: {text}

            Extract these exact fields:
            - form_type: type of form
            - applicant_name: person's name
            - contact_info: contact details
            - form_fields: other form data

            Return JSON format:""",
        }

        prompt = prompts.get(doc_type, prompts["form"])

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
        """Extract using Hugging Face"""

        prompt = f"Extract {doc_type} information from: {text[:300]}...\nJSON:"

        try:
            result = self.hf_generator(
                prompt, max_length=200, num_return_sequences=1, truncation=True
            )

            response = result[0]["generated_text"]
            return self._parse_json_response(response)

        except Exception as e:
            return {"error": str(e), "raw_response": ""}

    def _extract_with_gpt4(self, text: str, doc_type: str) -> Dict[str, Any]:
        """GPT-4 intelligent extraction using LangChain (YOUR ORIGINAL METHOD)"""

        # Document-specific prompts
        prompts = {
            "invoice": """
            Extract invoice information from this text and return JSON:
            - vendor_name: company name
            - invoice_number: invoice number  
            - total_amount: total amount (number only)
            - invoice_date: date
            - customer_info: customer details
            
            Text: {text}
            
            Return only valid JSON:
            """,
            "contract": """
            Extract contract information from this text and return JSON:
            - parties: list of contract parties
            - contract_type: type of contract
            - effective_date: start date
            - key_terms: important terms
            
            Text: {text}
            
            Return only valid JSON:
            """,
            "form": """
            Extract form information from this text and return JSON:
            - form_type: type of form
            - applicant_name: person's name
            - contact_info: contact details
            - form_fields: other form data
            
            Text: {text}
            
            Return only valid JSON:
            """,
        }

        # Get appropriate prompt
        prompt_template = prompts.get(doc_type, prompts["form"])

        # Create LangChain prompt and chain
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
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
