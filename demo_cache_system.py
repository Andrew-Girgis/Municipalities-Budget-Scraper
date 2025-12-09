"""Demonstrate the URL caching system."""
import json
from pathlib import Path
from src.utils import URLCache, FileHandler, setup_logger

logger = setup_logger(__name__)


def main():
    """Demonstrate cache functionality."""
    
    cache = URLCache()
    file_handler = FileHandler()
    
    print("\n" + "="*80)
    print(" "*25 + "🗄️  CACHE SYSTEM DEMO")
    print("="*80)
    
    # Show cache statistics
    cache_file = Path("url_cache.json")
    if cache_file.exists():
        with open(cache_file) as f:
            cache_data = json.load(f)
        
        print(f"\n📊 Cache Statistics:")
        print(f"   Total municipalities cached: {len(cache_data)}")
        print(f"   Cache file size: {cache_file.stat().st_size / 1024:.2f} KB")
        
        total_docs = sum(len(m['financial_documents']) for m in cache_data.values())
        print(f"   Total documents cached: {total_docs}")
        
        print("\n" + "-"*80)
        
        for csd_name, data in sorted(cache_data.items()):
            print(f"\n🏛️  {csd_name}")
            print(f"   📍 Parent: {data['parent_link'][:70]}...")
            print(f"   📄 Documents: {len(data['financial_documents'])}")
            print(f"   🕒 Updated: {data['last_updated']}")
            
            docs = data['financial_documents']
            for year in sorted(docs.keys(), reverse=True):
                url = docs[year]
                filename = Path(url).name[:50]
                print(f"      • {year}: {filename}...")
            
            # Check local files
            pdf_folder = Path(f"data/{csd_name}")
            if pdf_folder.exists():
                pdfs = list(pdf_folder.glob("*.pdf"))
                total_size = sum(p.stat().st_size for p in pdfs) / 1024 / 1024
                print(f"   💾 Local: {len(pdfs)} PDFs ({total_size:.2f} MB)")
    else:
        print("\n⚠️  No cache file found - run a scrape to create it")
    
    print("\n" + "="*80)
    print(" "*20 + "📖 HOW THE CACHE SYSTEM WORKS")
    print("="*80)
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ WORKFLOW COMPARISON                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ WITHOUT CACHE (First Run):                                                 │
│   1. Firecrawl search for municipality                    [~10-15s]        │
│   2. Playwright opens browser, navigates to site          [~5-10s]         │
│   3. Extract PDFs (direct, dropdowns, archives)           [~5-10s]         │
│   4. Download PDFs via HTTP GET                           [~5-20s]         │
│   5. Save URLs to cache                                   [~0.1s]          │
│   ────────────────────────────────────────────────                          │
│   Total Time: ~30-60 seconds                                               │
│   API Costs: Firecrawl ($0.10-0.50) + OpenAI ($0.01-0.05)                 │
│                                                                             │
│ WITH CACHE (Subsequent Runs):                                              │
│   1. Load URLs from cache                                 [~0.1s]          │
│   2. Download PDFs via HTTP GET (skip existing)           [~2-5s]          │
│   ────────────────────────────────────────────────                          │
│   Total Time: ~2-5 seconds (10x faster!)                                   │
│   API Costs: $0 (no API calls needed!)                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CACHE STRUCTURE                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ url_cache.json:                                                             │
│ {                                                                           │
│   "Calgary": {                                                              │
│     "CSD": "Calgary",                                                       │
│     "parent_link": "https://calgary.ca/financialreports",                  │
│     "financial_documents": {                                                │
│       "2024": "https://calgary.ca/.../2024-report.pdf",                    │
│       "2023": "https://calgary.ca/.../2023-report.pdf"                     │
│     },                                                                      │
│     "last_updated": "2025-12-08T22:16:41",                                 │
│     "metadata": {                                                           │
│       "discovery_method": "playwright_enhanced",                            │
│       "total_found": 2                                                      │
│     }                                                                       │
│   }                                                                         │
│ }                                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ DATA FOLDER STRUCTURE                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ data/                                                                       │
│ ├── Calgary/                                                                │
│ │   ├── 2024-municipal-fiscal-gap-report.pdf                               │
│ │   ├── 2023-Municipal-Fiscal-Gap-Report.pdf                               │
│ │   └── metadata.json                                                       │
│ ├── Toronto/                                                                │
│ │   ├── 2024-City-of-Toronto-Financial-Report.pdf                          │
│ │   ├── 2023-City-of-Toronto-Financial-Report.pdf                          │
│ │   └── metadata.json                                                       │
│ └── ...                                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    print("\n" + "="*80)
    print(" "*25 + "💡 USAGE EXAMPLES")
    print("="*80)
    
    print("""
# First run (builds cache):
python scrape_with_playwright.py --municipality "Calgary"
→ Full workflow: search → extract → download → cache

# Second run (uses cache):
python scrape_with_playwright.py --municipality "Calgary"
→ Fast: load cache → download missing files

# Process top 10:
python scrape_with_playwright.py --top 10
→ Builds cache for all 10, subsequent runs are fast

# View what's in the cache:
python demo_cache_system.py
    """)
    
    print("\n" + "="*80)
    print(" "*25 + "🎯 KEY BENEFITS")
    print("="*80)
    
    print("""
✓ Speed: 10x faster on subsequent runs
✓ Cost: No repeated API calls (Firecrawl/OpenAI)
✓ Reliability: Cached URLs work offline
✓ Sharing: Commit cache to git for team collaboration
✓ Updates: Easy to refresh individual municipalities
✓ Smart: Only downloads missing PDFs
    """)
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
