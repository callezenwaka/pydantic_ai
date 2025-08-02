# backend/src/core/textract_core.py
"""
Core utilities - moved from old utils.py
"""

# Just move your existing extract_text_from_file function here
from pathlib import Path
from fastapi import HTTPException

def extract_text_from_file(file_path: Path, file_ext: str) -> str:
    """Extract text from uploaded file with better error handling"""
    
    if file_ext == '.txt':
        return file_path.read_text(encoding='utf-8')
    
    elif file_ext == '.pdf':
        try:
            from pypdf import PdfReader
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF processing error: {str(e)}")
    
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        try:
            import pytesseract
            from PIL import Image
            
            print(f"🔍 Processing image: {file_path}")
            print(f"🔍 File exists: {file_path.exists()}")
            print(f"🔍 File size: {file_path.stat().st_size if file_path.exists() else 'N/A'}")
            
            # Test if we can open the image first
            with Image.open(file_path) as image:
                print(f"🔍 Image mode: {image.mode}")
                print(f"🔍 Image size: {image.size}")
                
                # Convert problematic formats
                if image.mode in ['CMYK', 'P']:
                    image = image.convert('RGB')
                
                # Try OCR
                text = pytesseract.image_to_string(image)
                print(f"🔍 Extracted text length: {len(text)}")
                
                return text if text.strip() else "No text found in image"
                
        except ImportError:
            raise HTTPException(status_code=500, detail="pytesseract/PIL not installed for image processing")
        except Exception as e:
            print(f"❌ OCR Error: {e}")
            error_msg = str(e)
            if "Corrupt JPEG" in error_msg or "premature end" in error_msg:
                return "This image appears to be corrupted. Please try uploading a different image or retaking the photo."
            else:
                return f"Unable to process this image: {error_msg}"
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")