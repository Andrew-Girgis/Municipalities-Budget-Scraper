# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Verify Setup
```bash
python test_setup.py
```
This checks that all components are working correctly.

### 2. View Existing Data
```bash
python view_data.py --stats
```
See what documents you already have downloaded.

### 3. Run Your First Scrape

**Test with one municipality:**
```bash
python main.py --municipality Toronto
```

**Scrape all configured municipalities:**
```bash
python main.py
```

## 📊 Common Commands

### View downloaded documents
```bash
# List all municipalities
python view_data.py

# View specific municipality
python view_data.py --municipality Toronto

# Show statistics
python view_data.py --stats
```

### Run scraper
```bash
# Scrape specific municipality
python main.py -m Mississauga

# Scrape all with debug logging
python main.py --log-level DEBUG

# Use custom config file
python main.py --config my_config.yaml
```

## 🔧 Configuration

### Add a new municipality

Edit `municipalities.yaml`:

```yaml
municipalities:
  # ... existing municipalities ...
  
  - name: YourCity
    website: https://yourcity.ca
    search_paths:
      - /budget/financial-reports
    document_patterns:
      - "annual report"
      - "financial statements"
    year_range:
      start: 2015
      end: 2024
```

Then run:
```bash
python main.py -m YourCity
```

## 📁 Project Files

- `main.py` - Main scraper script
- `test_setup.py` - Verify installation
- `view_data.py` - View downloaded data
- `municipalities.yaml` - Municipality configurations
- `.env` - Your API keys (keep secret!)
- `data/` - Downloaded PDFs organized by municipality
- `logs/` - Scraper logs

## 🐛 Troubleshooting

### "Import could not be resolved"
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "API key not found"
Check that `.env` file exists and contains:
```
FIRECRAWL_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### No documents found
1. Check logs in `logs/scraper_YYYYMMDD.log`
2. Verify `search_paths` in `municipalities.yaml`
3. Try adjusting `document_patterns` to match the municipality's terminology

## 💡 Tips

1. **Start small**: Test with one municipality before running all
2. **Check logs**: Always review logs after scraping to catch any issues
3. **Monitor API usage**: Both Firecrawl and OpenAI have usage limits
4. **Update yearly**: Add new year to `year_range.end` as new reports are published

## 📚 Next Steps

- Review `README.md` for detailed documentation
- Check `logs/` directory for scraping details
- Explore `src/` directory to understand the code structure
- Customize `municipalities.yaml` for your needs

## ❓ Need Help?

1. Check the logs in `logs/` directory
2. Run with debug logging: `python main.py --log-level DEBUG`
3. Open an issue on GitHub
