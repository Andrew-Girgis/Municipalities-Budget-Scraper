"""Generic municipality scraper."""
from typing import List, Dict, Optional, Any
from pathlib import Path
from urllib.parse import urljoin
import re

from ..utils import FirecrawlClient, OpenAIClient, FileHandler, setup_logger
from ..config import MunicipalityConfig

logger = setup_logger(__name__)


class MunicipalityScraper:
    """Scraper for municipality financial documents."""
    
    def __init__(
        self,
        config: MunicipalityConfig,
        firecrawl_client: FirecrawlClient,
        openai_client: OpenAIClient,
        file_handler: FileHandler
    ):
        """
        Initialize municipality scraper.
        
        Args:
            config: Municipality configuration
            firecrawl_client: Firecrawl API client
            openai_client: OpenAI API client
            file_handler: File handler for downloads
        """
        self.config = config
        self.firecrawl = firecrawl_client
        self.openai = openai_client
        self.file_handler = file_handler
        self.found_documents: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized scraper for {config.name}")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape financial documents for the municipality.
        
        Returns:
            List of found documents with metadata
        """
        logger.info(f"Starting scrape for {self.config.name}")
        
        # Build list of URLs to search
        urls_to_search = self._build_search_urls()
        
        # Search each URL for financial documents
        for url in urls_to_search:
            logger.info(f"Searching: {url}")
            self._search_url(url)
        
        # Download found documents
        downloaded = self._download_documents()
        
        logger.info(f"Scrape complete for {self.config.name}. Found {len(self.found_documents)} documents, downloaded {downloaded}")
        
        return self.found_documents
    
    def _build_search_urls(self) -> List[str]:
        """
        Build list of URLs to search based on configuration.
        
        Returns:
            List of URLs
        """
        urls = []
        
        # Add base website
        urls.append(self.config.website)
        
        # Add search paths
        for path in self.config.search_paths:
            full_url = urljoin(self.config.website, path)
            urls.append(full_url)
        
        return urls
    
    def _search_url(self, url: str) -> None:
        """
        Search a URL for financial documents.
        
        Args:
            url: URL to search
        """
        try:
            # Crawl the URL
            pages = self.firecrawl.crawl_website(
                url,
                max_depth=2,
                limit=15,
                include_paths=self.config.search_paths if self.config.search_paths else None
            )
            
            # Analyze each page
            for page in pages:
                self._analyze_page(page)
                
        except Exception as e:
            logger.error(f"Error searching {url}: {str(e)}")
    
    def _analyze_page(self, page: Dict[str, Any]) -> None:
        """
        Analyze a page for financial documents.
        
        Args:
            page: Page data from Firecrawl
        """
        try:
            page_url = page.get('metadata', {}).get('sourceURL', '')
            content = page.get('markdown', '')
            
            if not content:
                return
            
            # Use OpenAI to identify financial documents
            analysis = self.openai.identify_financial_documents(
                content,
                page_url,
                self.config.document_patterns
            )
            
            if analysis.get('has_financial_documents'):
                documents = analysis.get('documents', [])
                
                for doc in documents:
                    # Normalize URL
                    doc_url = doc.get('url', '')
                    if doc_url and not doc_url.startswith('http'):
                        doc_url = urljoin(page_url, doc_url)
                    
                    # Check if it's a PDF
                    if doc_url and '.pdf' in doc_url.lower():
                        # Extract year if not provided
                        year = doc.get('year')
                        if not year or year == 'unknown':
                            year = self._extract_year_from_url(doc_url)
                        
                        # Add to found documents
                        doc_info = {
                            'url': doc_url,
                            'year': year,
                            'document_type': doc.get('document_type', 'Unknown'),
                            'confidence': doc.get('confidence', 'medium'),
                            'source_page': page_url
                        }
                        
                        # Avoid duplicates
                        if not any(d['url'] == doc_url for d in self.found_documents):
                            self.found_documents.append(doc_info)
                            logger.info(f"Found document: {doc_url} ({year})")
                
        except Exception as e:
            logger.error(f"Error analyzing page: {str(e)}")
    
    def _extract_year_from_url(self, url: str) -> Optional[str]:
        """
        Extract year from URL or filename.
        
        Args:
            url: URL to analyze
        
        Returns:
            Year string or None
        """
        # Look for 4-digit year in URL
        year_match = re.search(r'20\d{2}', url)
        if year_match:
            return year_match.group(0)
        
        # Try using OpenAI
        year = self.openai.extract_year_from_text(url)
        return str(year) if year else None
    
    def _download_documents(self) -> int:
        """
        Download all found documents.
        
        Returns:
            Number of successfully downloaded documents
        """
        downloaded_count = 0
        
        for doc in self.found_documents:
            try:
                url = doc['url']
                year = doc.get('year')
                
                # Parse year to int if possible
                year_int = None
                if year:
                    try:
                        # Handle year ranges like "2023-2024"
                        if '-' in str(year):
                            year_int = int(str(year).split('-')[0])
                        else:
                            year_int = int(year)
                    except (ValueError, TypeError):
                        pass
                
                # Download the PDF
                filepath = self.file_handler.download_pdf(
                    url,
                    self.config.name,
                    year=year_int
                )
                
                if filepath:
                    # Save metadata
                    metadata = {
                        'source_url': url,
                        'year': year,
                        'document_type': doc.get('document_type'),
                        'confidence': doc.get('confidence'),
                        'source_page': doc.get('source_page')
                    }
                    
                    self.file_handler.save_metadata(
                        self.config.name,
                        filepath.name,
                        metadata
                    )
                    
                    downloaded_count += 1
                    doc['downloaded'] = True
                    doc['filepath'] = str(filepath)
                else:
                    doc['downloaded'] = False
                    
            except Exception as e:
                logger.error(f"Error downloading document {doc.get('url')}: {str(e)}")
                doc['downloaded'] = False
        
        return downloaded_count
