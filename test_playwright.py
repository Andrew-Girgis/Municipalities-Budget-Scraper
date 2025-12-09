#!/usr/bin/env python3
"""
Test script for Playwright-based scraping workflow.

This script tests the new CSV loader and Playwright integration.
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import setup_logger, MunicipalityCSVLoader
from src.utils.playwright_client import PlaywrightClient

logger = setup_logger("test_playwright", log_level="INFO")


def test_csv_loader():
    """Test CSV loader."""
    logger.info("Testing CSV loader...")
    try:
        csv_loader = MunicipalityCSVLoader("municipalities_clean.csv")
        logger.info(f"✓ Loaded CSV with {len(csv_loader.df)} municipalities")
        
        # Test get by name
        toronto = csv_loader.get_municipality_by_name("Toronto")
        if toronto:
            logger.info(f"✓ Found Toronto: population {toronto['pop']:,}")
        
        # Test top N
        top_10 = csv_loader.get_top_n_by_population(10)
        logger.info(f"✓ Top 10 municipalities by population:")
        for i, muni in enumerate(top_10, 1):
            logger.info(f"   {i}. {muni['name']} - {muni['pop']:,}")
        
        return True
    except Exception as e:
        logger.error(f"✗ CSV loader test failed: {e}")
        return False


async def test_playwright():
    """Test Playwright client and Firecrawl search."""
    logger.info("\nTesting Firecrawl search + Playwright navigation...")
    try:
        # Test Firecrawl search first
        from src.utils import FirecrawlClient
        firecrawl = FirecrawlClient()
        
        search_query = "Toronto previous financial statements"
        logger.info(f"Testing Firecrawl search: {search_query}")
        results = firecrawl.web_search(search_query, limit=3)
        
        if not results:
            logger.error("✗ Firecrawl search returned no results")
            return False
        
        logger.info(f"✓ Firecrawl found {len(results)} results")
        first_url = results[0]
        logger.info(f"  Top result: {first_url}")
        
        # Now test Playwright navigation
        async with PlaywrightClient(headless=False) as playwright:
            logger.info("✓ Playwright browser started")
            
            logger.info(f"Navigating to: {first_url}")
            budget_links = await playwright.find_budget_page_links(first_url)
            logger.info(f"✓ Found {len(budget_links)} budget-related links")
            
            if budget_links:
                for i, link in enumerate(budget_links[:5], 1):
                    logger.info(f"   {i}. {link}")
        
        logger.info("✓ Playwright browser closed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("="*60)
    logger.info("PLAYWRIGHT SETUP VERIFICATION")
    logger.info("="*60)
    
    tests = [
        ("CSV Loader", test_csv_loader, False),
        ("Playwright Client", test_playwright, True),
    ]
    
    results = []
    for test_name, test_func, is_async in tests:
        try:
            if is_async:
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("="*60)
    
    if passed == total:
        logger.info("\n🎉 All tests passed! Playwright scraper is ready to use.")
        logger.info("Run 'python scrape_with_playwright.py --help' to see usage options.")
        return 0
    else:
        logger.error("\n⚠️ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
