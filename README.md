# Municipalities Budget Scraper

An intelligent web scraper for automatically discovering and downloading annual audited financial reports from Canadian municipality websites. Built in support of @BuildCanada.

## Features

- 🤖 **AI-Powered Document Discovery**: Uses OpenAI to intelligently identify financial documents on municipality websites
- 🔍 **Smart Crawling**: Leverages Firecrawl API for efficient and comprehensive web crawling
- 🌐 **Browser Automation**: Playwright integration for handling interactive web elements
- 🎯 **Multi-Strategy PDF Extraction**: Handles PDFs in various formats (direct links, dropdowns, archive pages)
- 📊 **CSV-Based Configuration**: Process all 3,696 Canadian municipalities from CSV data
- 📁 **Organized Storage**: Automatically organizes documents by municipality
- 🪵 **Comprehensive Logging**: Detailed logs for monitoring and debugging
- ✨ **Intelligent PDF Renaming**: Automatically extracts text and generates standardized filenames
- 💾 **URL Caching**: Stores discovered URLs for 10x faster subsequent runs

## Intelligent PDF Renaming

**NEW:** PDFs are automatically renamed using AI-powered text extraction to follow a standardized format:

```
{CSD_Name}_{Document_Type}_{Year}.pdf
```

**Example:**
- Before: `2023-financial-report.pdf`
- After: `Calgary_Consolidated_Financial_Statements_2023.pdf`

See [PDF_RENAMING_GUIDE.md](PDF_RENAMING_GUIDE.md) for complete documentation.

### Quick Start

```bash
# Auto-rename enabled by default
python scrape_with_playwright.py --municipality "Calgary"

# Rename existing PDFs
python rename_existing_pdfs.py --dry-run

# Demo the system
python demo_pdf_renaming.py
```

## Enhanced PDF Extraction

The scraper uses a **4-strategy approach** to handle different website formats:

1. **Direct PDF Links** - Scans page for immediate PDF links
2. **Dropdown/Accordion Expansion** - Clicks expandable elements to reveal hidden PDFs
3. **Archive Link Discovery** - Finds "previous years" and "archive" pages
4. **Budget Page Discovery** - Identifies related pages for comprehensive crawling

See [ENHANCED_EXTRACTION.md](ENHANCED_EXTRACTION.md) for detailed documentation.

## Project Structure

```
Municipalities-Budget-Scraper/
├── main.py                      # Main orchestration script
├── requirements.txt             # Python dependencies
├── municipalities.yaml          # Municipality configurations
├── .env                        # API keys (not in git)
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── config_loader.py    # Configuration management
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── municipality_scraper.py  # Generic scraper implementation
│   └── utils/
│       ├── __init__.py
│       ├── firecrawl_client.py # Firecrawl API wrapper
│       ├── openai_client.py    # OpenAI API wrapper
│       ├── file_handler.py     # File download & organization
│       └── logger.py           # Logging configuration
├── data/                       # Downloaded documents (by municipality)
│   ├── Toronto/
│   │   ├── *.pdf
│   │   └── metadata.json
│   └── Mississauga/
│       ├── *.pdf
│       └── metadata.json
└── logs/                       # Application logs
    └── scraper_YYYYMMDD.log
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Andrew-Girgis/Municipalities-Budget-Scraper.git
cd Municipalities-Budget-Scraper
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file in the project root with your API keys:

```env
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Scrape All Municipalities

```bash
python main.py
```

### Scrape a Specific Municipality

```bash
python main.py --municipality Toronto
```

### Command-Line Options

```bash
python main.py --help
```

Options:
- `-m, --municipality NAME`: Scrape a specific municipality
- `-c, --config PATH`: Path to configuration file (default: `municipalities.yaml`)
- `-l, --log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)

## Adding New Municipalities

Edit `municipalities.yaml` and add a new entry:

```yaml
municipalities:
  - name: Ottawa
    website: https://ottawa.ca
    search_paths:
      - /en/city-hall/budget-and-taxes/financial-reports
    document_patterns:
      - "annual financial report"
      - "consolidated financial statements"
      - "audited financial statements"
    year_range:
      start: 2015
      end: 2024
```

## Configuration

### Municipality Configuration Fields

- **name**: Municipality name (used for folder naming)
- **website**: Base URL of municipality website
- **search_paths**: Specific URL paths to search for financial documents
- **document_patterns**: Keywords to identify relevant documents
- **year_range**: Range of years to search for documents

## How It Works

1. **Configuration Loading**: Reads municipality settings from `municipalities.yaml`
2. **Web Crawling**: Uses Firecrawl to crawl configured URLs and search paths
3. **AI Analysis**: OpenAI analyzes page content to identify financial report PDFs
4. **Document Download**: Downloads identified PDFs to `data/{municipality}/`
5. **Metadata Storage**: Saves document metadata to `metadata.json` for tracking

## Metadata

Each municipality's `metadata.json` contains:
- Source URL of the document
- Detected year
- Document type
- Confidence level of identification
- Download timestamp
- Source page URL

## Logs

Logs are stored in `logs/scraper_YYYYMMDD.log` with:
- Scraping progress
- API calls and responses
- Errors and warnings
- Download status

## Dependencies

- `firecrawl-py`: Web crawling and scraping
- `openai`: Document identification and analysis
- `pydantic`: Configuration validation
- `pyyaml`: Configuration file parsing
- `python-dotenv`: Environment variable management
- `requests`: HTTP requests for downloads

## Contributing

Feel free to open issues or submit pull requests for:
- Adding new municipalities
- Improving document detection
- Enhancing error handling
- Adding new features

## License

This project is created in support of @BuildCanada initiative.

## Troubleshooting

### Import Errors
Make sure you're in the virtual environment and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### API Rate Limits
Both Firecrawl and OpenAI have rate limits. The scraper includes error handling, but you may need to:
- Reduce `limit` in crawl settings
- Add delays between requests
- Check your API quota

### Missing Documents
If expected documents aren't found:
- Check `logs/` for errors
- Verify `search_paths` in `municipalities.yaml`
- Adjust `document_patterns` to match municipality's terminology
- Increase `max_depth` or `limit` in crawl settings
