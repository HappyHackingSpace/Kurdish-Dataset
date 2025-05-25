import io
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_content):
    """
    Extract text from PDF content in memory
    Args:
        pdf_content: PDF file content as bytes
    Returns:
        str: Extracted text from PDF
    """
    try:
        # Create a BytesIO object from the PDF content
        pdf_file = io.BytesIO(pdf_content)
        
        # Create PDF reader object
        pdf_reader = PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise 