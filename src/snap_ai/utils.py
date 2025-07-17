from pathlib import Path
from fastapi import HTTPException
from pypdf import PdfReader


def extract_text_from_file(file_path: Path, file_ext: str) -> str:
    """Extract text from uploaded file"""
    
    if file_ext == '.txt':
        return file_path.read_text(encoding='utf-8')
    
    elif file_ext == '.pdf':
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            raise HTTPException(status_code=500, detail="PyPDF2 not installed for PDF processing")
    
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except ImportError:
            raise HTTPException(status_code=500, detail="pytesseract/PIL not installed for image processing")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
