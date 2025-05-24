import os
import logging
import PyPDF2
from typing import Optional

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text from a PDF file with improved error handling and logging.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return None
    
    try:
        with open(pdf_path, 'rb') as file:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                logger.warning(f"PDF is encrypted: {pdf_path}")
                return "PDF is encrypted and cannot be processed."
            
            # Get number of pages
            num_pages = len(pdf_reader.pages)
            if num_pages == 0:
                logger.warning(f"PDF has no pages: {pdf_path}")
                return "PDF has no pages."
            
            # Extract text from each page
            text = []
            for page_num in range(num_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
                    else:
                        logger.warning(f"No text extracted from page {page_num + 1} in {pdf_path}")
                except Exception as e:
                    logger.error(f"Error extracting text from page {page_num + 1}: {str(e)}")
            
            # Combine all text
            extracted_text = "\n".join(text)
            
            if not extracted_text.strip():
                logger.warning(f"No text could be extracted from PDF: {pdf_path}")
                return "No text could be extracted from the PDF."
            
            return extracted_text
            
    except PyPDF2.PdfReadError as e:
        logger.error(f"Error reading PDF: {str(e)}")
        return f"Error reading PDF: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error processing PDF: {str(e)}")
        return f"Error processing PDF: {str(e)}" 