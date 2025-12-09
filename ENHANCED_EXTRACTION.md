# Enhanced PDF Extraction Implementation

## Overview

The scraper now uses a **multi-strategy approach** to extract PDFs from municipality websites, solving the problem of varying website formats (direct links, dropdowns, archive pages, etc.).

## Implementation Details

### New Methods in `PlaywrightClient`

#### `extract_all_pdfs(url)` - Main Extraction Method
Combines 4 strategies to find PDFs:

1. **Direct PDF Links** - Scans page for immediate PDF links
2. **Dropdown/Accordion Expansion** - Clicks expandable elements containing budget keywords
3. **Archive Link Discovery** - Finds links to "previous years", "archive", "view all" pages
4. **Budget Page Discovery** - Identifies related budget pages for Firecrawl crawling

**Returns:**
```python
{
    'pdf_urls': [...],      # PDFs found directly
    'budget_urls': [...]    # URLs for deeper crawling
}
```

#### `_find_direct_pdf_links(page, base_url)`
- Scans all `<a>` tags for `.pdf` links
- Converts relative URLs to absolute
- Returns set of PDF URLs

#### `_expand_all_dropdowns(page)`
- Clicks elements with `aria-expanded="false"`
- Opens all `<details>` elements
- Expands accordions and collapsible sections
- Only expands if contains budget-related keywords

#### `_find_archive_links(page, base_url)`
- Searches for links with keywords: "archive", "previous", "past", "historical", "view all"
- Filters for budget-related content
- Returns URLs (not PDFs) for further processing

#### `_find_budget_links(page, base_url)`
- Finds non-PDF links related to budgets/finances
- Keywords: "budget", "financial", "finance", "annual report", "fiscal"
- Returns URLs for comprehensive crawling

### Updated Scraper Workflow

**Previous:** Firecrawl search → Playwright navigate → find budget links → crawl each

**New:** Firecrawl search → Playwright **enhanced extraction** → process direct PDFs + crawl budget URLs

The new workflow in `PlaywrightMunicipalityScraper.scrape()`:
1. Search with Firecrawl (avoids CAPTCHA)
2. Navigate to top result with Playwright
3. **Use multi-strategy extraction** to get PDFs and URLs
4. Add direct PDFs to results immediately
5. Crawl discovered budget URLs with Firecrawl for comprehensive coverage
6. Analyze crawled pages with OpenAI
7. Download all found PDFs

## Test Results

### Calgary
- **Direct PDFs found:** 2
- **Budget URLs for crawling:** 14
- **Sample PDFs:**
  - Municipal-Fiscal-Gap-Report-2023.pdf
  - municipal-fiscal-gap-report-update.pdf

### Toronto  
- **Direct PDFs found:** 6
- **Budget URLs for crawling:** 30
- **Sample PDFs:**
  - 2024-Consolidated-Financial-Statements.pdf
  - 2024-Trust-Fund-Statements.pdf
  - 2023-City-of-Toronto-Financial-Report.pdf

## Key Features

✓ **Handles Direct Links** - Finds PDFs immediately visible on page  
✓ **Expands Dropdowns** - Opens collapsible sections to reveal hidden PDFs  
✓ **Discovers Archives** - Identifies links to previous years' documents  
✓ **Finds Related Pages** - Discovers budget-related pages for deep crawling  
✓ **Timeout Resilient** - Uses `domcontentloaded` + fallback for slow pages  
✓ **Error Handling** - Gracefully handles failures, returns partial results  

## Usage

### Direct Usage
```python
from src.utils.playwright_client import PlaywrightClient

async with PlaywrightClient(headless=True) as playwright:
    result = await playwright.extract_all_pdfs(url)
    
    # Process direct PDFs
    for pdf_url in result['pdf_urls']:
        print(f"Found PDF: {pdf_url}")
    
    # Crawl budget URLs for more PDFs
    for budget_url in result['budget_urls']:
        # Use Firecrawl to crawl these pages
        pass
```

### Via Scraper
```bash
# Single municipality
python scrape_with_playwright.py --municipality "Calgary"

# Top N by population
python scrape_with_playwright.py --top 5

# With visible browser
python scrape_with_playwright.py --municipality "Toronto" --visible
```

## Testing

Run comprehensive tests:
```bash
# Test enhanced extraction
python test_enhanced_extraction.py

# Quick demonstration
python demo_extraction.py
```

## Benefits

1. **Handles Variation** - Works with different website structures
2. **Higher Success Rate** - Multiple strategies increase PDF discovery
3. **Immediate Results** - Direct PDFs found first, no waiting
4. **Comprehensive** - Budget URLs ensure nothing is missed
5. **Efficient** - Playwright for interactive, Firecrawl for comprehensive

## Technical Notes

- **Timeout:** 60s page load + 10s network idle (with fallback)
- **Wait Strategy:** `domcontentloaded` → try `networkidle` → continue anyway
- **Keyword Matching:** Case-insensitive, checks both text and href
- **URL Normalization:** Converts relative URLs to absolute
- **Deduplication:** Uses sets to avoid duplicate PDFs/URLs
