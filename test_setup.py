#!/usr/bin/env python3
"""
Example/test script to verify the scraper setup.

This script performs basic checks to ensure:
- Configuration loads correctly
- API clients initialize properly
- File structure is accessible
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config, get_municipality_config
from src.utils import FirecrawlClient, OpenAIClient, FileHandler, setup_logger

logger = setup_logger("test_setup", log_level="INFO")


def test_configuration():
    """Test configuration loading."""
    logger.info("Testing configuration loading...")
    try:
        config = load_config("municipalities.yaml")
        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  Found {len(config.municipalities)} municipalities:")
        for muni in config.municipalities:
            logger.info(f"    - {muni.name}")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration loading failed: {e}")
        return False


def test_api_clients():
    """Test API client initialization."""
    logger.info("\nTesting API clients...")
    
    # Test Firecrawl
    try:
        firecrawl = FirecrawlClient()
        logger.info("✓ Firecrawl client initialized")
    except Exception as e:
        logger.error(f"✗ Firecrawl client failed: {e}")
        return False
    
    # Test OpenAI
    try:
        openai = OpenAIClient()
        logger.info("✓ OpenAI client initialized")
    except Exception as e:
        logger.error(f"✗ OpenAI client failed: {e}")
        return False
    
    return True


def test_file_handler():
    """Test file handler."""
    logger.info("\nTesting file handler...")
    try:
        file_handler = FileHandler()
        logger.info("✓ File handler initialized")
        
        # Check data directory
        if file_handler.base_data_dir.exists():
            logger.info(f"✓ Data directory exists: {file_handler.base_data_dir}")
        
        return True
    except Exception as e:
        logger.error(f"✗ File handler failed: {e}")
        return False


def test_municipality_config():
    """Test individual municipality configuration."""
    logger.info("\nTesting municipality configuration...")
    try:
        toronto_config = get_municipality_config("Toronto")
        logger.info("✓ Toronto configuration loaded")
        logger.info(f"  Website: {toronto_config.website}")
        logger.info(f"  Search paths: {len(toronto_config.search_paths)}")
        logger.info(f"  Year range: {toronto_config.year_range.start}-{toronto_config.year_range.end}")
        return True
    except Exception as e:
        logger.error(f"✗ Municipality config failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("="*60)
    logger.info("SETUP VERIFICATION")
    logger.info("="*60)
    
    tests = [
        ("Configuration", test_configuration),
        ("API Clients", test_api_clients),
        ("File Handler", test_file_handler),
        ("Municipality Config", test_municipality_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
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
        logger.info("\n🎉 All tests passed! Your scraper is ready to use.")
        logger.info("Run 'python main.py --help' to see usage options.")
        return 0
    else:
        logger.error("\n⚠️ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
