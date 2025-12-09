"""Playwright-based municipality scraper."""
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils import FirecrawlClient, OpenAIClient, FileHandler, URLCache, PDFTextExtractor, setup_logger
from ..utils.playwright_client import PlaywrightClient
from ..utils.csv_loader import MunicipalityCSVLoader

logger = setup_logger(__name__)


class PlaywrightMunicipalityScraper:
    """Scraper using Playwright for search + Firecrawl/OpenAI for document discovery."""
    
    def __init__(
        self,
        municipality_data: Dict[str, Any],
        firecrawl_client: FirecrawlClient,
        openai_client: OpenAIClient,
        file_handler: FileHandler,
        url_cache: Optional[URLCache] = None,
        headless: bool = True,
        auto_rename_pdfs: bool = True
    ):
        """
        Initialize scraper.
        
        Args:
            municipality_data: Municipality data from CSV
            firecrawl_client: Firecrawl API client
            openai_client: OpenAI API client
            file_handler: File handler for downloads
            url_cache: URL cache for storing discovered links
            headless: Run browser in headless mode
            auto_rename_pdfs: Automatically rename PDFs after download
        """
        self.municipality = municipality_data
        self.name = municipality_data['name']
        self.firecrawl = firecrawl_client
        self.openai = openai_client
        self.file_handler = file_handler
        self.url_cache = url_cache or URLCache()
        self.headless = headless
        self.auto_rename_pdfs = auto_rename_pdfs
        self.pdf_extractor = PDFTextExtractor() if auto_rename_pdfs else None
        self.found_documents: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized Playwright scraper for {self.name}")
        if auto_rename_pdfs:
            logger.info("Auto-rename PDFs: ENABLED")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape financial documents for the municipality.
        
        Returns:
            List of found documents with metadata
        """
        logger.info(f"="*60)
        logger.info(f"Starting scrape for {self.name}")
        logger.info(f"="*60)
        
        # Check cache first
        if self.url_cache.has_municipality(self.name):
            logger.info(f"✓ Found {self.name} in cache, using cached URLs")
            cached_docs = self.url_cache.get_documents(self.name)
            parent_link = self.url_cache.get_parent_link(self.name)
            
            logger.info(f"Cache has {len(cached_docs)} documents")
            logger.info(f"Parent link: {parent_link}")
            
            # Download PDFs from cached URLs
            for year, pdf_url in cached_docs.items():
                doc_info = {
                    'url': pdf_url,
                    'year': year,
                    'document_type': 'Financial Document',
                    'confidence': 'high',
                    'source_page': parent_link,
                    'discovery_method': 'cache'
                }
                self.found_documents.append(doc_info)
            
            # Download documents
            downloaded = self._download_documents()
            
            logger.info(f"="*60)
            logger.info(f"Cache-based scrape complete for {self.name}")
            logger.info(f"Downloaded: {downloaded} documents")
            logger.info(f"="*60)
            return self.found_documents
        
        # Step 1: Use Firecrawl to search (avoids Google CAPTCHA)
        logger.info("No cache found, performing full scrape...")
        search_query = f"{self.name} previous financial statements"
        logger.info(f"Searching with Firecrawl: {search_query}")
        
        search_results = self.firecrawl.web_search(search_query, limit=5)
        
        if not search_results:
            logger.warning(f"No search results found for {self.name}")
            return []
        
        logger.info(f"Found {len(search_results)} search results")
        for i, url in enumerate(search_results[:3], 1):
            logger.info(f"  {i}. {url}")
        
        # Step 2: Use Playwright to navigate and extract PDFs with multiple strategies
        direct_pdfs = []
        budget_urls = []
        async with PlaywrightClient(headless=self.headless) as playwright:
            # Navigate to first result and use enhanced extraction
            first_result = search_results[0]
            logger.info(f"Navigating with Playwright to: {first_result}")
            
            # Use multi-strategy PDF extraction
            extraction_result = await playwright.extract_all_pdfs(first_result)
            direct_pdfs = extraction_result['pdf_urls']
            budget_urls = extraction_result['budget_urls']
            
            logger.info(f"Playwright extraction: {len(direct_pdfs)} PDFs, {len(budget_urls)} URLs for crawling")
            
            # Add directly found PDFs to our results
            for pdf_url in direct_pdfs:
                # Try to extract year from URL
                year = self._extract_year_from_url(pdf_url)
                
                doc_info = {
                    'url': pdf_url,
                    'year': year,
                    'document_type': 'Financial Document',
                    'confidence': 'high',
                    'source_page': first_result,
                    'discovery_method': 'playwright_direct'
                }
                if not any(d['url'] == pdf_url for d in self.found_documents):
                    self.found_documents.append(doc_info)
                    logger.info(f"Direct PDF found: {pdf_url} (year: {year})")
        
        # Step 3: Use Firecrawl to crawl budget URLs for more comprehensive coverage
        urls_to_crawl = budget_urls[:5]  # Limit to first 5 URLs
        if not urls_to_crawl and not direct_pdfs:
            # If no budget URLs found, crawl the original search results
            urls_to_crawl = search_results[:3]
        
        for url in urls_to_crawl:
            self._crawl_and_analyze_url(url)
        
        # Step 4: Download found documents
        downloaded = self._download_documents()
        
        # Step 5: Update cache with discovered documents
        if self.found_documents and search_results:
            financial_docs = {}
            for i, doc in enumerate(self.found_documents):
                year = doc.get('year') or f'doc_{i+1}'
                # If multiple docs with same year, add index
                key = str(year)
                counter = 1
                while key in financial_docs:
                    key = f"{year}_{counter}"
                    counter += 1
                financial_docs[key] = doc['url']
            
            self.url_cache.update_municipality(
                csd_name=self.name,
                parent_link=search_results[0],
                financial_documents=financial_docs,
                metadata={
                    'discovery_method': 'playwright_enhanced',
                    'total_found': len(self.found_documents),
                    'direct_pdfs': len(direct_pdfs),
                    'crawled_urls': len(urls_to_crawl)
                }
            )
            logger.info(f"✓ Updated cache for {self.name} with {len(financial_docs)} documents")
        
        logger.info(f"="*60)
        logger.info(f"Scrape complete for {self.name}")
        logger.info(f"Found: {len(self.found_documents)} documents")
        logger.info(f"Downloaded: {downloaded} documents")
        logger.info(f"="*60)
        
        return self.found_documents
    
    def _crawl_and_analyze_url(self, url: str) -> None:
        """
        Crawl URL with Firecrawl and analyze for PDFs.
        
        Args:
            url: URL to crawl
        """
        try:
            logger.info(f"Crawling: {url}")
            
            # Crawl with Firecrawl
            pages = self.firecrawl.crawl_website(
                url,
                max_depth=2,
                limit=10
            )
            
            # Analyze each page
            for page in pages:
                self._analyze_page(page)
                
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
    
    def _analyze_page(self, page: Dict[str, Any]) -> None:
        """
        Analyze page for financial documents using OpenAI.
        
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
                ["annual financial report", "audited financial statements", "budget"]
            )
            
            if analysis.get('has_financial_documents'):
                documents = analysis.get('documents', [])
                
                for doc in documents:
                    doc_url = doc.get('url', '')
                    
                    # Normalize URL
                    if doc_url and not doc_url.startswith('http'):
                        from urllib.parse import urljoin
                        doc_url = urljoin(page_url, doc_url)
                    
                    # Check if it's a PDF
                    if doc_url and '.pdf' in doc_url.lower():
                        doc_info = {
                            'url': doc_url,
                            'year': doc.get('year'),
                            'document_type': doc.get('document_type', 'Unknown'),
                            'confidence': doc.get('confidence', 'medium'),
                            'source_page': page_url
                        }
                        
                        # Avoid duplicates
                        if not any(d['url'] == doc_url for d in self.found_documents):
                            self.found_documents.append(doc_info)
                            logger.info(f"Found document: {doc_url} ({doc.get('year', 'unknown')})")
                
        except Exception as e:
            logger.error(f"Error analyzing page: {str(e)}")
    
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
                        if '-' in str(year):
                            year_int = int(str(year).split('-')[0])
                        else:
                            year_int = int(year)
                    except (ValueError, TypeError):
                        pass
                
                # Download the PDF
                filepath = self.file_handler.download_pdf(
                    url,
                    self.name,
                    year=year_int
                )
                
                if filepath:
                    # Save metadata
                    metadata = {
                        'source_url': url,
                        'year': year,
                        'document_type': doc.get('document_type'),
                        'confidence': doc.get('confidence'),
                        'source_page': doc.get('source_page'),
                        'municipality_data': self.municipality
                    }
                    
                    self.file_handler.save_metadata(
                        self.name,
                        filepath.name,
                        metadata
                    )
                    
                    # Auto-rename PDF if enabled
                    if self.auto_rename_pdfs and self.pdf_extractor:
                        self._rename_downloaded_pdf(filepath)
                    
                    downloaded_count += 1
                    doc['downloaded'] = True
                    doc['filepath'] = str(filepath)
                else:
                    doc['downloaded'] = False
                    
            except Exception as e:
                logger.error(f"Error downloading document {doc.get('url')}: {str(e)}")
                doc['downloaded'] = False
        
        return downloaded_count
    
    def _rename_downloaded_pdf(self, filepath: Path) -> None:
        """
        Rename a downloaded PDF using text extraction and OpenAI analysis.
        
        Args:
            filepath: Path to downloaded PDF file
        """
        try:
            filename = filepath.name
            logger.info(f"Auto-renaming: {filename}")
            
            # Extract text from PDF
            pdf_text = self.pdf_extractor.extract_text_from_pdf(filepath, max_chars=2000)
            
            if not pdf_text:
                logger.warning(f"Could not extract text from {filename} - skipping rename")
                return
            
            # Rename using file handler
            new_path = self.file_handler.rename_pdf_with_extracted_info(
                municipality_name=self.name,
                current_filename=filename,
                pdf_text=pdf_text,
                openai_client=self.openai,
                update_metadata=True
            )
            
            if new_path:
                logger.info(f"✓ Renamed to: {new_path.name}")
            else:
                logger.warning(f"Failed to rename {filename}")
                
        except Exception as e:
            logger.error(f"Error renaming {filepath.name}: {str(e)}")
    
    def _extract_year_from_url(self, url: str) -> Optional[str]:
        """
        Extract year from URL or filename.
        
        Args:
            url: PDF URL
        
        Returns:
            Year as string or None
        """
        import re
        
        # Look for 4-digit years (2000-2099)
        years = re.findall(r'20[0-9]{2}', url)
        
        if years:
            # Return the most recent year found
            return max(years)
        
        return None


def run_playwright_scraper(municipality_name: str, csv_path: str = "municipalities_clean.csv", headless: bool = True) -> List[Dict[str, Any]]:
    """
    Helper function to run playwright scraper for a municipality.
    
    Args:
        municipality_name: Name of municipality
        csv_path: Path to CSV file
        headless: Run browser in headless mode
    
    Returns:
        List of found documents
    """
    # Load municipality data
    csv_loader = MunicipalityCSVLoader(csv_path)
    muni_data = csv_loader.get_municipality_by_name(municipality_name)
    
    if not muni_data:
        raise ValueError(f"Municipality '{municipality_name}' not found in CSV")
    
    # Initialize clients
    firecrawl = FirecrawlClient()
    openai = OpenAIClient()
    file_handler = FileHandler()
    
    # Create scraper
    scraper = PlaywrightMunicipalityScraper(
        municipality_data=muni_data,
        firecrawl_client=firecrawl,
        openai_client=openai,
        file_handler=file_handler,
        headless=headless
    )
    
    # Run scraper (async)
    return asyncio.run(scraper.scrape())
