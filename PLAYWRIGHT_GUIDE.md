# Playwright Scraper Guide

## New CSV-Based Workflow

The scraper now uses your `municipalities_clean.csv` file with 3,696 Canadian municipalities and Playwright for automated browser navigation.

## How It Works

1. **Load Municipality Data** from CSV (all CSDs in Canada)
2. **Playwright Search**: Opens browser, searches "{Municipality} budget" on Google
3. **Navigate & Discover**: Finds budget-related links on the official website
4. **Firecrawl**: Crawls discovered pages for comprehensive coverage
5. **OpenAI Analysis**: Identifies which PDFs are annual financial reports
6. **Download**: Saves PDFs to `data/{Municipality-name}/` folders

## Quick Start

### Test a Single Municipality

```bash
# With visible browser (recommended first time)
python scrape_with_playwright.py --municipality "Toronto" --visible

# Headless mode (faster)
python scrape_with_playwright.py --municipality "Toronto"
```

### Scrape Top Municipalities by Population

```bash
# Top 5 municipalities
python scrape_with_playwright.py --top 5 --visible

# Top 10 in headless mode
python scrape_with_playwright.py --top 10

# Top 50 (will take a while!)
python scrape_with_playwright.py --top 50
```

## Command Options

```bash
python scrape_with_playwright.py --help
```

- `--municipality NAME` or `-m NAME` - Scrape specific municipality
- `--top N` or `-t N` - Scrape top N municipalities by population
- `--csv PATH` or `-c PATH` - Use custom CSV file (default: municipalities_clean.csv)
- `--visible` or `-v` - Show browser window (useful for debugging/CAPTCHA)
- `--log-level LEVEL` or `-l LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR)

## Examples

```bash
# Scrape Ottawa with visible browser
python scrape_with_playwright.py -m "Ottawa" -v

# Scrape top 20 municipalities
python scrape_with_playwright.py -t 20

# Scrape Calgary with debug logging
python scrape_with_playwright.py -m "Calgary" -l DEBUG

# Use custom CSV file
python scrape_with_playwright.py -m "Vancouver" -c my_municipalities.csv
```

## Municipality Names

Municipality names in the CSV include:
- Toronto
- Montréal
- Calgary
- Ottawa
- Edmonton
- Winnipeg
- Mississauga
- Vancouver
- Brampton
- Hamilton
- ... and 3,686 more!

View all municipalities:
```bash
# In Python
from src.utils.csv_loader import MunicipalityCSVLoader
loader = MunicipalityCSVLoader()
top_50 = loader.get_top_n_by_population(50)
for m in top_50:
    print(f"{m['name']} - Population: {m['pop']:,}")
```

## CAPTCHA Handling

If Google shows a CAPTCHA:
1. Run with `--visible` flag
2. The browser will pause for 10 seconds
3. Manually complete the CAPTCHA
4. The scraper will continue automatically

## Notes

- **API Usage**: Each municipality uses Firecrawl and OpenAI API calls
- **Rate Limiting**: Small delays are built in between municipalities
- **Headless vs Visible**: Headless is faster but visible helps with debugging
- **CSV Data**: The CSV contains population, province codes, and other metadata
- **Output**: PDFs are saved to `data/{Municipality}/` folders

## Troubleshooting

### "Municipality not found in CSV"
Check the exact spelling in the CSV file. Names are case-insensitive but must match exactly.

### Browser automation fails
- Try with `--visible` to see what's happening
- Check internet connection
- Ensure Playwright browsers are installed: `playwright install chromium`

### Too many API calls
- Start with top 5-10 municipalities
- Use `--top` with smaller numbers
- Monitor your Firecrawl/OpenAI API usage

## Advanced: Province Filtering

You can filter by province using the CSV loader:

```python
from src.utils.csv_loader import MunicipalityCSVLoader

loader = MunicipalityCSVLoader()

# Ontario municipalities (PR_UID = '35')
ontario = loader.filter_by_province('35')
print(f"Found {len(ontario)} Ontario municipalities")

# Quebec municipalities (PR_UID = '24')
quebec = loader.filter_by_province('24')
```

Province codes:
- 10: Newfoundland and Labrador
- 11: Prince Edward Island
- 12: Nova Scotia
- 13: New Brunswick
- 24: Quebec
- 35: Ontario
- 46: Manitoba
- 47: Saskatchewan
- 48: Alberta
- 59: British Columbia
