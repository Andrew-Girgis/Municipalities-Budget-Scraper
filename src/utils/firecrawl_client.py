"""Firecrawl API client for web scraping."""
import os
import time
import re
from typing import Dict, List, Optional, Any
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import requests
from .logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)


class FirecrawlClient:
    """Client for interacting with Firecrawl API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Firecrawl client.
        
        Args:
            api_key: Firecrawl API key. If not provided, reads from FIRECRAWL_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API key not found. Set FIRECRAWL_API_KEY environment variable.")
        
        self.client = FirecrawlApp(api_key=self.api_key)
        logger.info("Firecrawl client initialized")
    
    def scrape_url(self, url: str, formats: List[str] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Scrape a single URL with automatic retry on rate limits.
        
        Args:
            url: URL to scrape
            formats: List of formats to return (e.g., ['markdown', 'html'])
            max_retries: Maximum number of retry attempts for rate limits
        
        Returns:
            Scraped content dictionary
        """
        formats = formats or ['markdown', 'html']
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Scraping URL: {url}")
                result = self.client.scrape_url(url, params={'formats': formats})
                logger.debug(f"Successfully scraped {url}")
                return result
            except requests.Timeout as e:
                logger.warning(f"Timeout scraping {url}: {e}")
                raise
            except requests.ConnectionError as e:
                logger.error(f"Connection error scraping {url}: {e}")
                raise
            except Exception as e:
                # Check if it's a rate limit error
                error_msg = str(e)
                if 'rate limit' in error_msg.lower():
                    wait_time = self._extract_wait_time(error_msg)
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries - 1}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise
                else:
                    logger.exception(f"Unexpected error scraping {url}")
                    raise
        
        raise Exception(f"Failed to scrape {url} after {max_retries} attempts")
    
    def crawl_website(
        self, 
        url: str, 
        max_depth: int = 2,
        limit: int = 10,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Crawl a website starting from a URL with automatic retry on rate limits.
        
        Args:
            url: Starting URL for crawling
            max_depth: Maximum depth to crawl
            limit: Maximum number of pages to crawl
            include_paths: List of URL patterns to include
            exclude_paths: List of URL patterns to exclude
            max_retries: Maximum number of retry attempts for rate limits
        
        Returns:
            List of crawled page data
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Crawling website: {url} (max_depth={max_depth}, limit={limit})")
                
                # Start crawl job with correct parameter names for Firecrawl v2 API
                crawl_result = self.client.crawl(
                    url,
                    max_discovery_depth=max_depth,
                    limit=limit,
                    include_paths=include_paths,
                    exclude_paths=exclude_paths,
                    scrape_options={'formats': ['markdown', 'html']},
                    poll_interval=5
                )
                
                if crawl_result and 'data' in crawl_result:
                    pages = crawl_result['data']
                    logger.info(f"Successfully crawled {len(pages)} pages from {url}")
                    return pages
                else:
                    logger.warning(f"No data returned from crawl of {url}")
                    return []
                    
            except requests.Timeout as e:
                logger.warning(f"Timeout crawling {url}: {e}")
                raise
            except requests.ConnectionError as e:
                logger.error(f"Connection error crawling {url}: {e}")
                raise
            except Exception as e:
                # Check if it's a rate limit error
                error_msg = str(e)
                if 'rate limit' in error_msg.lower():
                    wait_time = self._extract_wait_time(error_msg)
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries - 1}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise
                else:
                    logger.exception(f"Unexpected error crawling {url}")
                    raise
        
        raise Exception(f"Failed to crawl {url} after {max_retries} attempts")
    
    def search_for_links(
        self,
        url: str,
        keywords: List[str],
        max_depth: int = 2
    ) -> List[str]:
        """
        Search a website for links containing specific keywords.
        
        Args:
            url: Starting URL
            keywords: Keywords to search for in links/content
            max_depth: Maximum depth to crawl
        
        Returns:
            List of relevant URLs
        """
        try:
            pages = self.crawl_website(url, max_depth=max_depth, limit=20)
            relevant_urls = []
            
            for page in pages:
                page_url = page.get('metadata', {}).get('sourceURL', '')
                content = page.get('markdown', '').lower()
                
                # Check if any keyword appears in URL or content
                for keyword in keywords:
                    if keyword.lower() in page_url.lower() or keyword.lower() in content:
                        if page_url not in relevant_urls:
                            relevant_urls.append(page_url)
                            logger.debug(f"Found relevant URL: {page_url}")
                        break
            
            logger.info(f"Found {len(relevant_urls)} relevant URLs")
            return relevant_urls
            
        except Exception:
            logger.exception("Error searching for links")
            return []
    
    def web_search(self, query: str, limit: int = 5) -> List[str]:
        """
        Perform a web search using Firecrawl.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of URLs from search results
        """
        try:
            logger.info(f"Searching web for: {query}")
            
            # Use Firecrawl's search capability
            result = self.client.search(query)
            
            # Result is a SearchData object with a 'web' attribute containing SearchResultWeb objects
            if result and hasattr(result, 'web') and result.web:
                urls = [item.url for item in result.web if hasattr(item, 'url')]
                # Filter out Google/YouTube links
                filtered_urls = [
                    url for url in urls 
                    if 'google.com' not in url and 'youtube.com' not in url
                ]
                logger.info(f"Found {len(filtered_urls)} search results")
                return filtered_urls[:limit]
            else:
                logger.warning(f"No search results for: {query}")
                return []
                
        except Exception:
            logger.exception("Error performing web search")
            return []
    
    def _extract_wait_time(self, error_message: str) -> int:
        """
        Extract wait time from rate limit error message.
        
        Args:
            error_message: Error message containing rate limit info
        
        Returns:
            Wait time in seconds (default: 20s)
        """
        # Try to extract "retry after Xs" pattern
        match = re.search(r'retry after (\d+)s', error_message)
        if match:
            wait_time = int(match.group(1))
            # Add 2 second buffer
            return wait_time + 2
        
        # Try to extract reset time and calculate wait
        match = re.search(r'resets at ([^-]+)', error_message)
        if match:
            # If we can't parse the time, default to 20 seconds
            logger.debug(f"Rate limit resets at: {match.group(1)}")
            return 20
        
        # Default wait time
        logger.debug("Using default wait time of 20 seconds")
        return 20
