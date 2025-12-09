"""OpenAI API client for document analysis."""
import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv
from .logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        logger.info(f"OpenAI client initialized with model: {model}")
    
    def identify_financial_documents(
        self,
        page_content: str,
        page_url: str,
        document_patterns: List[str]
    ) -> Dict[str, Any]:
        """
        Use AI to identify if a page contains links to financial documents.
        
        Args:
            page_content: Content of the webpage
            page_url: URL of the page
            document_patterns: Expected document patterns/keywords
        
        Returns:
            Dictionary with analysis results including PDF links and metadata
        """
        try:
            prompt = f"""Analyze this webpage content and identify any links to annual audited financial reports or budget documents.

Page URL: {page_url}

Looking for documents matching these patterns:
{', '.join(document_patterns)}

Page content (markdown):
{page_content[:4000]}  # Limit content to avoid token limits

Please identify:
1. Any PDF links to financial/budget reports
2. The year(s) each document covers
3. The type of document (e.g., "Annual Financial Report", "Budget Highlights", etc.)

Respond in JSON format:
{{
    "has_financial_documents": true/false,
    "documents": [
        {{
            "url": "full URL to PDF",
            "year": "YYYY or YYYY-YYYY",
            "document_type": "type of document",
            "confidence": "high/medium/low"
        }}
    ]
}}"""

            logger.debug(f"Analyzing page: {page_url}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing government websites to find financial documents. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.debug(f"Found {len(result.get('documents', []))} documents on {page_url}")
            return result
            
        except Exception:
            logger.exception(f"Error analyzing page content from {page_url}")
            return {"has_financial_documents": False, "documents": []}
    
    def extract_year_from_text(self, text: str) -> Optional[int]:
        """
        Extract year from text using AI.
        
        Args:
            text: Text to analyze
        
        Returns:
            Extracted year or None
        """
        try:
            prompt = f"""Extract the primary year this financial document refers to from the following text.
Only return the 4-digit year number, nothing else.

Text: {text[:500]}

Year:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract years from document titles. Only respond with a 4-digit year or 'unknown'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10
            )
            
            year_str = response.choices[0].message.content.strip()
            
            # Try to parse as integer
            if year_str.isdigit() and len(year_str) == 4:
                return int(year_str)
            
            return None
            
        except Exception:
            logger.exception("Error extracting year from text")
            return None
    
    def categorize_document(self, filename: str, content_preview: str = "") -> str:
        """
        Categorize a financial document type.
        
        Args:
            filename: Name of the document file
            content_preview: Preview of document content (if available)
        
        Returns:
            Document category/type
        """
        try:
            prompt = f"""Categorize this financial document into one of these types:
- Annual Financial Report
- Budget Highlights
- Consolidated Financial Statements
- Audited Financial Statements
- Popular Annual Report
- Other

Filename: {filename}
{f'Content preview: {content_preview[:200]}' if content_preview else ''}

Respond with just the category name."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You categorize municipal financial documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=20
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception:
            logger.exception(f"Error categorizing document: {filename}")
            return "Other"
    
    def generate_standardized_filename(
        self,
        pdf_text: str,
        csd_name: str,
        current_filename: str
    ) -> Dict[str, Any]:
        """
        Generate a standardized filename for a financial document based on its content.
        
        Analyzes PDF text to extract document type and year, then creates a filename
        following the pattern: {CSD_Name}_{Document_Type}_{Year}.pdf
        
        Args:
            pdf_text: Extracted text from the PDF (first ~2000 chars)
            csd_name: Census Subdivision name (municipality name)
            current_filename: Current filename (for fallback)
        
        Returns:
            Dictionary with:
                - filename: Standardized filename
                - document_type: Identified document type
                - year: Identified year
                - confidence: Confidence level (high/medium/low)
        """
        try:
            prompt = f"""Analyze this financial document text and extract key information.

Municipality/Organization: {csd_name}
Current filename: {current_filename}

Document text (first 2000 chars):
{pdf_text}

Please identify:
1. The PRIMARY year this document covers (fiscal year, reporting year)
2. The specific document type (be descriptive but concise)

Common document types for Canadian municipalities following PSAS:
- Consolidated Financial Statements
- Annual Financial Report
- Audited Financial Statements
- Budget Document
- Popular Annual Financial Report (PAFR)
- Financial Statement Discussion and Analysis
- Year End Financial Report
- Interim Financial Statements

Respond in JSON format:
{{
    "year": "YYYY or YYYY-YYYY for fiscal years",
    "document_type": "specific document type (3-5 words max)",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation of how you determined year and type"
}}

Important:
- For fiscal years like "Year ended December 31, 2023", use "2023"
- For fiscal years like "April 1, 2023 - March 31, 2024", use "2023-2024"
- Be specific with document type but keep it concise
- Use title case for document type"""

            logger.debug(f"Analyzing PDF text for standardized filename: {current_filename}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing Canadian public sector financial documents following PSAS. Extract document metadata accurately."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Clean up the document type for filename
            doc_type = result.get('document_type', 'Financial Document')
            doc_type = self._sanitize_for_filename(doc_type)
            
            # Clean up CSD name
            csd_clean = self._sanitize_for_filename(csd_name)
            
            # Get year
            year = result.get('year', 'Unknown_Year')
            
            # Create standardized filename
            standardized_name = f"{csd_clean}_{doc_type}_{year}.pdf"
            
            logger.info(f"Generated filename: {standardized_name} (confidence: {result.get('confidence', 'unknown')})")
            
            return {
                'filename': standardized_name,
                'document_type': result.get('document_type'),
                'year': year,
                'confidence': result.get('confidence', 'unknown'),
                'reasoning': result.get('reasoning', '')
            }
            
        except Exception:
            logger.exception(f"Error generating standardized filename for {current_filename}")
            # Fallback to a safe filename
            csd_clean = self._sanitize_for_filename(csd_name)
            return {
                'filename': f"{csd_clean}_Financial_Document.pdf",
                'document_type': 'Financial Document',
                'year': 'Unknown',
                'confidence': 'low',
                'reasoning': 'Error during analysis - see logs for details'
            }
    
    def _sanitize_for_filename(self, text: str) -> str:
        """
        Sanitize text for use in filename.
        
        Args:
            text: Text to sanitize
        
        Returns:
            Filename-safe text
        """
        import re
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        # Remove or replace invalid filename characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Remove multiple underscores
        text = re.sub(r'_+', '_', text)
        # Remove leading/trailing underscores
        text = text.strip('_')
        # Limit length (leave room for extension and year)
        if len(text) > 100:
            text = text[:100]
        return text
