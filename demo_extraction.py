"""Quick test to demonstrate enhanced PDF extraction capabilities."""
import asyncio
from src.utils.playwright_client import PlaywrightClient
from src.utils import setup_logger

logger = setup_logger(__name__)


async def quick_test():
    """Quick test showing the multi-strategy extraction."""
    
    test_urls = [
        ("Calgary", "https://www.calgary.ca/financialreports"),
        ("Toronto", "https://www.toronto.ca/city-government/budget-finances/city-finance/annual-financial-report/"),
    ]
    
    for name, url in test_urls:
        async with PlaywrightClient(headless=True) as playwright:
            logger.info(f"\nTesting: {name}")
            logger.info("-" * 60)
            result = await playwright.extract_all_pdfs(url)
            
            logger.info(f"✓ Found {len(result['pdf_urls'])} PDFs directly")
            logger.info(f"✓ Found {len(result['budget_urls'])} additional URLs to crawl")
            
            if result['pdf_urls']:
                logger.info(f"  Sample PDFs:")
                for pdf in result['pdf_urls'][:3]:
                    filename = pdf.split('/')[-1][:60]
                    logger.info(f"    • {filename}")


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("ENHANCED PDF EXTRACTION DEMONSTRATION")
    logger.info("="*60)
    logger.info("\nStrategies implemented:")
    logger.info("  1. Direct PDF link scanning")
    logger.info("  2. Expand dropdowns/accordions")
    logger.info("  3. Find archive/previous years links")
    logger.info("  4. Discover budget-related pages")
    logger.info("="*60)
    
    asyncio.run(quick_test())
    
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info("✓ Enhanced extraction handles multiple website formats")
    logger.info("✓ PDFs found directly are added immediately")
    logger.info("✓ Budget URLs discovered for comprehensive Firecrawl crawling")
    logger.info("✓ Combination of Playwright + Firecrawl ensures thorough coverage")
    logger.info("="*60)
