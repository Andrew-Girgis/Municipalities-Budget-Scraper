"""Test enhanced PDF extraction with multiple strategies."""
import asyncio
from src.utils.playwright_client import PlaywrightClient
from src.utils import setup_logger

logger = setup_logger(__name__)


async def test_calgary_extraction():
    """Test extraction on Calgary's financial reports page."""
    url = "https://www.calgary.ca/financialreports"
    
    async with PlaywrightClient(headless=True) as playwright:
        logger.info(f"Testing enhanced extraction on: {url}")
        result = await playwright.extract_all_pdfs(url)
        
        logger.info("="*60)
        logger.info("EXTRACTION RESULTS")
        logger.info("="*60)
        logger.info(f"Direct PDFs found: {len(result['pdf_urls'])}")
        for pdf in result['pdf_urls'][:10]:  # Show first 10
            logger.info(f"  - {pdf}")
        
        logger.info(f"\nBudget URLs for crawling: {len(result['budget_urls'])}")
        for budget_url in result['budget_urls'][:10]:  # Show first 10
            logger.info(f"  - {budget_url}")
        logger.info("="*60)


async def test_toronto_extraction():
    """Test extraction on Toronto's financial reports page."""
    url = "https://www.toronto.ca/city-government/budget-finances/city-finance/annual-financial-report/"
    
    async with PlaywrightClient(headless=True) as playwright:
        logger.info(f"Testing enhanced extraction on: {url}")
        result = await playwright.extract_all_pdfs(url)
        
        logger.info("="*60)
        logger.info("EXTRACTION RESULTS")
        logger.info("="*60)
        logger.info(f"Direct PDFs found: {len(result['pdf_urls'])}")
        for pdf in result['pdf_urls'][:10]:  # Show first 10
            logger.info(f"  - {pdf}")
        
        logger.info(f"\nBudget URLs for crawling: {len(result['budget_urls'])}")
        for budget_url in result['budget_urls'][:10]:  # Show first 10
            logger.info(f"  - {budget_url}")
        logger.info("="*60)


async def main():
    """Run tests."""
    logger.info("Testing enhanced PDF extraction strategies\n")
    
    logger.info("TEST 1: Calgary (may have dropdowns/archives)")
    await test_calgary_extraction()
    
    logger.info("\n\nTEST 2: Toronto (direct PDFs)")
    await test_toronto_extraction()
    
    logger.info("\n\nAll tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
