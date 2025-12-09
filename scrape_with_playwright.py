#!/usr/bin/env python3
"""
Main script for scraping with Playwright automation.

This script uses Playwright to search for municipality websites,
then uses Firecrawl and OpenAI to find and download financial documents.
"""
import argparse
import asyncio
import sys
from pathlib import Path

from src.utils import FirecrawlClient, OpenAIClient, FileHandler, URLCache, setup_logger
from src.utils.csv_loader import MunicipalityCSVLoader
from src.utils.playwright_client import PlaywrightClient
from src.scrapers.playwright_municipality_scraper import PlaywrightMunicipalityScraper

logger = setup_logger("playwright_scraper", log_level="INFO")


async def scrape_municipality(municipality_name: str, csv_path: str = "municipalities_clean.csv", headless: bool = True, auto_rename: bool = True) -> bool:
    """
    Scrape financial documents for a single municipality.
    
    Args:
        municipality_name: Name of the municipality
        csv_path: Path to CSV file
        headless: Run browser in headless mode
        auto_rename: Automatically rename PDFs using text extraction
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load municipality data
        csv_loader = MunicipalityCSVLoader(csv_path)
        muni_data = csv_loader.get_municipality_by_name(municipality_name)
        
        if not muni_data:
            logger.error(f"Municipality '{municipality_name}' not found in CSV")
            return False
        
        logger.info(f"Municipality: {muni_data['name']}")
        logger.info(f"Population: {muni_data['pop']:,}")
        logger.info(f"Province: {muni_data['PR_UID']}")
        
        # Initialize clients
        firecrawl = FirecrawlClient()
        openai = OpenAIClient()
        file_handler = FileHandler()
        url_cache = URLCache()
        
        # Check if folder exists
        if file_handler.municipality_folder_exists(municipality_name):
            existing_pdfs = file_handler.get_existing_pdfs(municipality_name)
            logger.info(f"✓ Folder exists with {len(existing_pdfs)} existing PDFs")
        else:
            logger.info("→ No existing folder, will create on download")
        
        # Create and run scraper
        scraper = PlaywrightMunicipalityScraper(
            municipality_data=muni_data,
            firecrawl_client=firecrawl,
            openai_client=openai,
            file_handler=file_handler,
            url_cache=url_cache,
            headless=headless,
            auto_rename_pdfs=auto_rename
        )
        
        documents = await scraper.scrape()
        
        # Summary
        logger.info(f"\nSummary for {municipality_name}:")
        logger.info(f"  Found: {len(documents)} documents")
        logger.info(f"  Downloaded: {sum(1 for d in documents if d.get('downloaded'))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error scraping {municipality_name}: {str(e)}", exc_info=True)
        return False


async def scrape_top_n(n: int = 10, csv_path: str = "municipalities_clean.csv", headless: bool = True, auto_rename: bool = True):
    """
    Scrape top N municipalities by population.
    
    Args:
        n: Number of municipalities to scrape
        csv_path: Path to CSV file
        headless: Run browser in headless mode
        auto_rename: Automatically rename PDFs using text extraction
    """
    try:
        csv_loader = MunicipalityCSVLoader(csv_path)
        top_municipalities = csv_loader.get_top_n_by_population(n)
        
        logger.info(f"Scraping top {n} municipalities by population")
        
        results = {}
        
        for i, muni in enumerate(top_municipalities, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"[{i}/{n}] Processing: {muni['name']}")
            logger.info(f"{'='*60}")
            
            success = await scrape_municipality(muni['name'], csv_path, headless, auto_rename)
            results[muni['name']] = success
            
            # Small delay between municipalities
            if i < n:
                await asyncio.sleep(2)
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("FINAL SUMMARY")
        logger.info(f"{'='*60}")
        
        for name, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            logger.info(f"  {name}: {status}")
        
        successful = sum(1 for s in results.values() if s)
        logger.info(f"\nTotal: {successful}/{len(results)} municipalities scraped successfully")
        
    except Exception as e:
        logger.error(f"Error in scrape_top_n: {str(e)}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape municipality financial reports using Playwright automation"
    )
    
    parser.add_argument(
        '--municipality',
        '-m',
        type=str,
        help='Name of specific municipality to scrape'
    )
    
    parser.add_argument(
        '--top',
        '-t',
        type=int,
        help='Scrape top N municipalities by population'
    )
    
    parser.add_argument(
        '--csv',
        '-c',
        type=str,
        default='municipalities_clean.csv',
        help='Path to CSV file (default: municipalities_clean.csv)'
    )
    
    parser.add_argument(
        '--visible',
        '-v',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )
    
    parser.add_argument(
        '--no-rename',
        action='store_true',
        help='Disable automatic PDF renaming (default: enabled)'
    )
    
    parser.add_argument(
        '--log-level',
        '-l',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Update log level
    global logger
    logger = setup_logger("playwright_scraper", log_level=args.log_level)
    
    # Verify CSV file exists
    if not Path(args.csv).exists():
        logger.error(f"CSV file not found: {args.csv}")
        sys.exit(1)
    
    headless = not args.visible
    auto_rename = not args.no_rename
    
    if auto_rename:
        logger.info("Auto-rename PDFs: ENABLED")
    else:
        logger.info("Auto-rename PDFs: DISABLED")
    
    # Run scraper
    if args.municipality:
        # Scrape single municipality
        success = asyncio.run(scrape_municipality(args.municipality, args.csv, headless, auto_rename))
        sys.exit(0 if success else 1)
    elif args.top:
        # Scrape top N
        asyncio.run(scrape_top_n(args.top, args.csv, headless, auto_rename))
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
