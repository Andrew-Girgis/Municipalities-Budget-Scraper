#!/usr/bin/env python3
"""
Main script for scraping municipality financial documents.

This script orchestrates the scraping process for all configured municipalities,
using Firecrawl for web crawling and OpenAI for intelligent document identification.
"""
import argparse
import sys
from pathlib import Path

from src.config import load_config, get_municipality_config
from src.utils import FirecrawlClient, OpenAIClient, FileHandler, setup_logger
from src.scrapers import MunicipalityScraper

logger = setup_logger("main", log_level="INFO")


def scrape_municipality(municipality_name: str, config_path: str = "municipalities.yaml") -> bool:
    """
    Scrape financial documents for a single municipality.
    
    Args:
        municipality_name: Name of the municipality to scrape
        config_path: Path to configuration file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"{'='*60}")
        logger.info(f"Starting scrape for: {municipality_name}")
        logger.info(f"{'='*60}")
        
        # Load configuration
        config = get_municipality_config(municipality_name, config_path)
        
        # Initialize clients
        firecrawl = FirecrawlClient()
        openai = OpenAIClient()
        file_handler = FileHandler()
        
        # Create scraper
        scraper = MunicipalityScraper(
            config=config,
            firecrawl_client=firecrawl,
            openai_client=openai,
            file_handler=file_handler
        )
        
        # Run scraper
        documents = scraper.scrape()
        
        # Summary
        logger.info(f"{'='*60}")
        logger.info(f"Summary for {municipality_name}:")
        logger.info(f"  Total documents found: {len(documents)}")
        logger.info(f"  Downloaded: {sum(1 for d in documents if d.get('downloaded'))}")
        logger.info(f"  Failed: {sum(1 for d in documents if not d.get('downloaded'))}")
        logger.info(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error scraping {municipality_name}: {str(e)}", exc_info=True)
        return False


def scrape_all(config_path: str = "municipalities.yaml") -> None:
    """
    Scrape all municipalities in the configuration.
    
    Args:
        config_path: Path to configuration file
    """
    try:
        # Load configuration
        config = load_config(config_path)
        
        logger.info(f"Found {len(config.municipalities)} municipalities to scrape")
        
        results = {}
        
        # Scrape each municipality
        for muni_config in config.municipalities:
            success = scrape_municipality(muni_config.name, config_path)
            results[muni_config.name] = success
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("FINAL SUMMARY")
        logger.info(f"{'='*60}")
        
        for name, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            logger.info(f"  {name}: {status}")
        
        successful = sum(1 for s in results.values() if s)
        logger.info(f"\nTotal: {successful}/{len(results)} municipalities scraped successfully")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Error in scrape_all: {str(e)}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape annual financial reports from municipality websites"
    )
    
    parser.add_argument(
        '--municipality',
        '-m',
        type=str,
        help='Name of specific municipality to scrape (scrapes all if not specified)'
    )
    
    parser.add_argument(
        '--config',
        '-c',
        type=str,
        default='municipalities.yaml',
        help='Path to configuration file (default: municipalities.yaml)'
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
    logger = setup_logger("main", log_level=args.log_level)
    
    # Verify config file exists
    if not Path(args.config).exists():
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Run scraper
    if args.municipality:
        # Scrape single municipality
        success = scrape_municipality(args.municipality, args.config)
        sys.exit(0 if success else 1)
    else:
        # Scrape all municipalities
        scrape_all(args.config)
        sys.exit(0)


if __name__ == "__main__":
    main()
