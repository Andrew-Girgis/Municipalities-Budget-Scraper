"""Playwright browser automation client."""
import asyncio
import time
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError
from .logger import setup_logger

logger = setup_logger(__name__)


class PlaywrightClient:
    """Client for browser automation using Playwright."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize Playwright client.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
        logger.info(f"Playwright client initialized (headless={headless})")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        logger.info("Browser started")
    
    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
    
    async def search_and_get_first_result(
        self,
        query: str,
        search_engine: str = "https://www.google.com"
    ) -> Optional[str]:
        """
        Search on search engine and return first result URL.
        
        Args:
            query: Search query
            search_engine: Search engine URL
        
        Returns:
            URL of first result or None
        """
        page = None
        try:
            page = await self.browser.new_page()
            
            # Go to search engine
            await page.goto(search_engine, wait_until='networkidle')
            logger.info(f"Searching for: {query}")
            
            # Wait for user to complete CAPTCHA if needed
            logger.info("Waiting 10 seconds for manual CAPTCHA completion if needed...")
            await asyncio.sleep(10)
            
            # Find search box and enter query
            search_box = await page.wait_for_selector('textarea[name="q"], input[name="q"]', timeout=10000)
            await search_box.fill(query)
            await search_box.press('Enter')
            
            # Wait for results
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)  # Longer delay for results to render
            
            # Get first result (skip ads) - try multiple selectors
            first_result = await page.query_selector('div#search a[href]:not([href*="google.com"]):not([href*="youtube.com"])')
            
            # If that doesn't work, try a broader selector
            if not first_result:
                first_result = await page.query_selector('div#rso a[href]')
            
            # Or try even broader
            if not first_result:
                first_result = await page.query_selector('a[href^="http"]:not([href*="google.com"])')
            
            if first_result:
                url = await first_result.get_attribute('href')
                logger.info(f"First result: {url}")
                await page.close()
                return url
            else:
                logger.warning(f"No results found for: {query}")
                await page.close()
                return None
                
        except TimeoutError as e:
            logger.error(f"Timeout searching for {query}: {str(e)}")
            if page:
                await page.close()
            return None
        except Exception as e:
            logger.error(f"Error searching for {query}: {str(e)}")
            if page:
                await page.close()
            return None
    
    async def find_budget_page_links(self, url: str) -> List[str]:
        """
        Navigate to URL and find links related to budgets/financial reports.
        
        Args:
            url: Starting URL
        
        Returns:
            List of relevant URLs
        """
        page = None
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            logger.info(f"Navigating to: {url}")
            
            # Wait a moment for dynamic content
            await asyncio.sleep(2)
            
            # Find all links
            links = await page.query_selector_all('a[href]')
            
            budget_keywords = [
                'budget', 'financial', 'finance', 'annual report',
                'audited', 'financial statement', 'fiscal'
            ]
            
            relevant_urls = set()
            relevant_urls.add(url)  # Always include the starting URL
            
            for link in links:
                href = await link.get_attribute('href')
                text = await link.text_content()
                
                if href and text:
                    text_lower = text.lower()
                    href_lower = href.lower()
                    
                    # Check if link text or URL contains budget keywords
                    if any(keyword in text_lower or keyword in href_lower for keyword in budget_keywords):
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            from urllib.parse import urljoin
                            full_url = urljoin(url, href)
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        relevant_urls.add(full_url)
                        logger.debug(f"Found relevant link: {full_url}")
            
            await page.close()
            logger.info(f"Found {len(relevant_urls)} relevant URLs")
            return list(relevant_urls)
            
        except Exception as e:
            logger.error(f"Error finding budget links on {url}: {str(e)}")
            if page:
                await page.close()
            return [url]  # Return at least the starting URL
    
    async def get_page_content(self, url: str) -> Optional[str]:
        """
        Get page content.
        
        Args:
            url: URL to fetch
        
        Returns:
            Page HTML content or None
        """
        page = None
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            content = await page.content()
            await page.close()
            return content
        except Exception as e:
            logger.error(f"Error getting page content from {url}: {str(e)}")
            if page:
                await page.close()
            return None
    
    async def extract_all_pdfs(self, url: str) -> Dict[str, Any]:
        """
        Extract PDFs using multiple strategies to handle different website formats.
        
        Strategies:
        1. Direct PDF links on the page
        2. Expand dropdowns/accordions and scan
        3. Navigate to archive/previous years pages
        4. Handle JavaScript-generated content
        
        Args:
            url: Starting URL
        
        Returns:
            Dictionary with 'pdf_urls' list and 'budget_urls' list for further crawling
        """
        page = None
        try:
            page = await self.browser.new_page()
            
            # Increase timeout for slow-loading pages
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            logger.info(f"Extracting PDFs from: {url}")
            
            # Wait for dynamic content with shorter timeout
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except TimeoutError:
                logger.warning("Page didn't reach networkidle state, continuing anyway")
            
            await asyncio.sleep(2)
            
            result = {
                'pdf_urls': set(),
                'budget_urls': set()
            }
            
            # Strategy 1: Find direct PDF links
            direct_pdfs = await self._find_direct_pdf_links(page, url)
            result['pdf_urls'].update(direct_pdfs)
            logger.info(f"Strategy 1 (Direct): Found {len(direct_pdfs)} PDFs")
            
            # Strategy 2: Expand dropdowns and accordions
            await self._expand_all_dropdowns(page)
            await asyncio.sleep(1)  # Wait for expansion
            expanded_pdfs = await self._find_direct_pdf_links(page, url)
            new_pdfs = expanded_pdfs - result['pdf_urls']
            result['pdf_urls'].update(new_pdfs)
            logger.info(f"Strategy 2 (Dropdowns): Found {len(new_pdfs)} additional PDFs")
            
            # Strategy 3: Find archive/previous years links
            archive_urls = await self._find_archive_links(page, url)
            result['budget_urls'].update(archive_urls)
            logger.info(f"Strategy 3 (Archive): Found {len(archive_urls)} archive URLs")
            
            # Strategy 4: Find budget-related pages for further crawling
            budget_urls = await self._find_budget_links(page, url)
            result['budget_urls'].update(budget_urls)
            logger.info(f"Strategy 4 (Budget pages): Found {len(budget_urls)} budget URLs")
            
            await page.close()
            
            # Convert sets to lists
            result['pdf_urls'] = list(result['pdf_urls'])
            result['budget_urls'] = list(result['budget_urls'])
            
            logger.info(f"Total extraction: {len(result['pdf_urls'])} PDFs, {len(result['budget_urls'])} URLs for crawling")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting PDFs from {url}: {str(e)}")
            if page:
                try:
                    await page.close()
                except Exception as close_error:
                    logger.debug(f"Failed to close page after error: {close_error}")
            return {'pdf_urls': [], 'budget_urls': [url]}
    
    async def _find_direct_pdf_links(self, page: Page, base_url: str) -> set:
        """Find all direct PDF links on the current page."""
        from urllib.parse import urljoin
        
        pdf_urls = set()
        
        # Find all links
        links = await page.query_selector_all('a[href]')
        
        for link in links:
            href = await link.get_attribute('href')
            if href and '.pdf' in href.lower():
                # Convert to absolute URL
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(base_url, href)
                
                pdf_urls.add(full_url)
                logger.debug(f"Found PDF: {full_url}")
        
        return pdf_urls
    
    async def _expand_all_dropdowns(self, page: Page):
        """Expand all dropdowns, accordions, and collapsible elements."""
        # Common selectors for expandable elements
        expandable_selectors = [
            'button[aria-expanded="false"]',
            'details:not([open])',
            '.accordion:not(.active)',
            '[class*="collapse"]:not(.show)',
            '[class*="expand"]',
            '[role="button"][aria-expanded="false"]',
        ]
        
        for selector in expandable_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        # Check if element contains budget-related text
                        text = await element.text_content()
                        if text and any(keyword in text.lower() for keyword in [
                            'budget', 'financial', 'finance', 'annual', 'report',
                            'previous', 'archive', 'fiscal', 'year'
                        ]):
                            await element.click()
                            await asyncio.sleep(0.5)  # Wait for expansion
                            logger.debug(f"Expanded element: {text[:50]}")
                    except Exception as e:
                        logger.debug(f"Failed to click expandable element: {e}")
            except Exception as e:
                logger.debug(f"Failed to expand elements: {e}")
        
        # Open all <details> elements
        try:
            await page.evaluate('''() => {
                document.querySelectorAll('details').forEach(el => el.open = true);
            }''')
        except Exception as e:
            logger.debug(f"Failed to expand <details> elements: {e}")
    
    async def _find_archive_links(self, page: Page, base_url: str) -> set:
        """Find links to archive or previous years pages."""
        from urllib.parse import urljoin
        
        archive_urls = set()
        archive_keywords = [
            'archive', 'previous', 'past', 'historical', 'older',
            'prior year', 'view all', 'see all', 'more'
        ]
        
        links = await page.query_selector_all('a[href]')
        
        for link in links:
            try:
                text = await link.text_content()
                href = await link.get_attribute('href')
                
                if text and href:
                    text_lower = text.lower()
                    
                    # Check if link text indicates archive/previous content
                    if any(keyword in text_lower for keyword in archive_keywords):
                        # Also check if it's related to budgets
                        if any(keyword in text_lower for keyword in [
                            'budget', 'financial', 'finance', 'report', 'fiscal'
                        ]):
                            # Convert to absolute URL
                            if href.startswith('http'):
                                full_url = href
                            else:
                                full_url = urljoin(base_url, href)
                            
                            # Don't include PDFs here (they'll be found separately)
                            if '.pdf' not in full_url.lower():
                                archive_urls.add(full_url)
                                logger.debug(f"Found archive link: {full_url}")
            except Exception as e:
                logger.debug(f"Failed to process archive link: {e}")
        
        return archive_urls
    
    async def _find_budget_links(self, page: Page, base_url: str) -> set:
        """Find budget-related page links (not PDFs)."""
        from urllib.parse import urljoin
        
        budget_urls = set()
        budget_keywords = [
            'budget', 'financial', 'finance', 'annual report',
            'audited', 'financial statement', 'fiscal'
        ]
        
        links = await page.query_selector_all('a[href]')
        
        for link in links:
            try:
                href = await link.get_attribute('href')
                text = await link.text_content()
                
                if href and text:
                    text_lower = text.lower()
                    href_lower = href.lower()
                    
                    # Skip PDFs (they're handled separately)
                    if '.pdf' in href_lower:
                        continue
                    
                    # Check if link is budget-related
                    if any(keyword in text_lower or keyword in href_lower for keyword in budget_keywords):
                        # Convert to absolute URL
                        if href.startswith('http'):
                            full_url = href
                        elif href.startswith('/'):
                            full_url = urljoin(base_url, href)
                        else:
                            continue
                        
                        budget_urls.add(full_url)
                        logger.debug(f"Found budget link: {full_url}")
            except Exception as e:
                logger.debug(f"Failed to process budget link: {e}")
        
        return budget_urls
