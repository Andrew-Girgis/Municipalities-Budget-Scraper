"""PDF text extraction utilities using pdfminer.six."""
from pathlib import Path
from typing import Optional
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
from .logger import setup_logger

logger = setup_logger(__name__)


class PDFTextExtractor:
    """Handles PDF text extraction operations."""
    
    def __init__(self):
        """Initialize PDF text extractor."""
        logger.info("PDFTextExtractor initialized")
    
    def extract_text_from_pdf(
        self,
        pdf_path: Path,
        max_chars: int = 2000,
        page_numbers: Optional[list] = None
    ) -> Optional[str]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            max_chars: Maximum characters to extract (default 2000 for first pages)
            page_numbers: List of page numbers to extract (None = all pages)
        
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return None
            
            logger.debug(f"Extracting text from: {pdf_path.name}")
            
            # Extract text from PDF
            # pdfminer.six extracts text preserving layout
            text = extract_text(
                str(pdf_path),
                page_numbers=page_numbers,
                maxpages=3  # Only extract first 3 pages for efficiency
            )
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from {pdf_path.name} - may be scanned/image-based")
                return None
            
            # Clean the text
            text = self._clean_extracted_text(text)
            
            # Limit to max_chars
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.debug(f"Truncated text to {max_chars} chars")
            
            logger.debug(f"Successfully extracted {len(text)} chars from {pdf_path.name}")
            return text
            
        except PDFSyntaxError as e:
            logger.error(f"PDF syntax error in {pdf_path.name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {str(e)}")
            return None
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean extracted PDF text by removing excessive whitespace and noise.
        
        Args:
            text: Raw extracted text
        
        Returns:
            Cleaned text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Replace multiple newlines with single newline
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove lines that are just dots or underscores (common in headers/footers)
        lines = text.split('\n')
        cleaned_lines = [
            line for line in lines 
            if not re.match(r'^[._\-\s]{5,}$', line)
        ]
        text = '\n'.join(cleaned_lines)
        
        return text.strip()
    
    def extract_first_page_text(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text only from the first page of a PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Extracted text from first page or None if extraction fails
        """
        return self.extract_text_from_pdf(
            pdf_path,
            max_chars=1500,
            page_numbers=[0]  # First page only
        )
    
    def is_text_based_pdf(self, pdf_path: Path) -> bool:
        """
        Check if PDF is text-based (not scanned image).
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            True if text can be extracted, False otherwise
        """
        text = self.extract_first_page_text(pdf_path)
        
        # Consider it text-based if we get at least 100 chars
        if text and len(text.strip()) >= 100:
            return True
        
        logger.warning(f"PDF appears to be image-based (scanned): {pdf_path.name}")
        return False
