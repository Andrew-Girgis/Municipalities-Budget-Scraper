# PDF Intelligent Renaming System

## Overview

This system automatically extracts text from downloaded PDFs and uses OpenAI to generate standardized, descriptive filenames that follow the pattern:

```
{CSD_Name}_{Document_Type}_{Year}.pdf
```

**Example:**
- Original: `2023-financial-report.pdf`
- Renamed: `Calgary_Consolidated_Financial_Statements_2023.pdf`

## Why This Matters

Following @BuildCanada's goal to collect **every financial statement from Canadian public bodies**, standardized filenames ensure:

1. **Consistency** - All documents follow the same naming convention
2. **Discoverability** - File names clearly indicate content, municipality, and year
3. **Organization** - Easy to sort, search, and manage thousands of documents
4. **Metadata Preservation** - Document type and year extracted directly from content
5. **PSAS Compliance** - Identifies Public Sector Accounting Standards documents accurately

## Components

### 1. PDFTextExtractor (`src/utils/pdf_text_extractor.py`)

Extracts text from PDFs using `pdfminer.six`:

```python
from src.utils import PDFTextExtractor

extractor = PDFTextExtractor()

# Extract first 2000 chars from PDF
text = extractor.extract_text_from_pdf(pdf_path, max_chars=2000)

# Check if PDF is text-based (not scanned)
is_text = extractor.is_text_based_pdf(pdf_path)
```

**Features:**
- Extracts first 3 pages for efficiency
- Cleans text (removes excessive whitespace, headers/footers)
- Handles PDF syntax errors gracefully
- Detects scanned/image-based PDFs

### 2. OpenAI Intelligent Naming (`src/utils/openai_client.py`)

Analyzes extracted text to generate standardized filenames:

```python
from src.utils import OpenAIClient

openai = OpenAIClient()

result = openai.generate_standardized_filename(
    pdf_text=extracted_text,
    csd_name="Calgary",
    current_filename="2023-audit.pdf"
)

# Returns:
# {
#   'filename': 'Calgary_Audited_Financial_Statements_2023.pdf',
#   'document_type': 'Audited Financial Statements',
#   'year': '2023',
#   'confidence': 'high',
#   'reasoning': 'Document title clearly states...'
# }
```

**Document Types Recognized:**
- Consolidated Financial Statements
- Annual Financial Report
- Audited Financial Statements
- Budget Document
- Popular Annual Financial Report (PAFR)
- Financial Statement Discussion and Analysis
- Year End Financial Report
- Interim Financial Statements

**Year Handling:**
- Single years: `2023` → `2023`
- Fiscal years: `2023-2024` → `2023-2024`
- Detects year from document content, not just filename

### 3. FileHandler Rename Method (`src/utils/file_handler.py`)

Coordinates the entire rename process:

```python
from src.utils import FileHandler, OpenAIClient, PDFTextExtractor

file_handler = FileHandler()
openai = OpenAIClient()
extractor = PDFTextExtractor()

# Extract text
pdf_text = extractor.extract_text_from_pdf(pdf_path)

# Rename with extracted info
new_path = file_handler.rename_pdf_with_extracted_info(
    municipality_name="Calgary",
    current_filename="old_name.pdf",
    pdf_text=pdf_text,
    openai_client=openai,
    update_metadata=True
)
```

**Features:**
- Handles filename collisions (adds `_1`, `_2` suffix)
- Updates `metadata.json` with:
  - Original filename
  - Standardized filename
  - Document type
  - Year
  - Confidence level
  - Reasoning
  - Rename timestamp
- Preserves existing metadata

## Usage

### Option 1: Automatic Renaming During Scraping

**Enabled by default** - PDFs are automatically renamed after download:

```bash
# Auto-rename enabled (default)
python scrape_with_playwright.py --municipality "Calgary"

# Disable auto-rename
python scrape_with_playwright.py --municipality "Calgary" --no-rename
```

### Option 2: Post-Process Existing PDFs

Rename all existing PDFs in `data/` folders:

```bash
# Dry run - see what would be renamed
python rename_existing_pdfs.py --dry-run

# Rename all PDFs
python rename_existing_pdfs.py

# Rename specific municipality
python rename_existing_pdfs.py --municipality "Calgary"
```

**Output:**
```
Processing: 2023-financial-report.pdf
Extracted 1847 chars from 2023-financial-report.pdf
Analyzing 2023-financial-report.pdf for intelligent renaming...
Generated filename: Calgary_Consolidated_Financial_Statements_2023.pdf (confidence: high)
Renamed: 2023-financial-report.pdf -> Calgary_Consolidated_Financial_Statements_2023.pdf
✓ Updated metadata for Calgary_Consolidated_Financial_Statements_2023.pdf
```

## Metadata Tracking

Each renamed PDF has metadata saved in `metadata.json`:

```json
{
  "Calgary_Consolidated_Financial_Statements_2023.pdf": {
    "original_filename": "2023-financial-report.pdf",
    "standardized_filename": "Calgary_Consolidated_Financial_Statements_2023.pdf",
    "document_type": "Consolidated Financial Statements",
    "document_year": "2023",
    "rename_confidence": "high",
    "rename_reasoning": "Document clearly states 'Consolidated Financial Statements for the year ended December 31, 2023'",
    "renamed_at": "2025-12-08T15:30:45.123456",
    "source_url": "https://example.com/2023-report.pdf",
    "year": "2023",
    "confidence": "high",
    "source_page": "https://example.com/financials",
    "municipality_data": {...}
  }
}
```

## Architecture

### Workflow: Auto-Rename During Scraping

```
1. Download PDF
   ↓
2. Save metadata
   ↓
3. Extract text (PDFTextExtractor)
   ↓
4. Analyze with OpenAI (generate_standardized_filename)
   ↓
5. Rename file
   ↓
6. Update metadata.json
```

### Workflow: Post-Process Existing PDFs

```
1. Scan data/ folders
   ↓
2. For each PDF:
   - Check if already standardized
   - Extract text (2000 chars)
   - Analyze with OpenAI
   - Rename file
   - Update metadata
   ↓
3. Generate summary report
```

## Error Handling

### Scanned/Image PDFs
If PDF is image-based (no extractable text):
- Logs warning: `"No text extracted - may be scanned/image-based"`
- Skips rename
- Original filename preserved

### API Errors
If OpenAI API fails:
- Logs error with details
- Returns fallback filename: `{CSD_Name}_Financial_Document.pdf`
- Sets confidence to `"low"`

### Filename Collisions
If target filename exists:
- Appends counter: `_1`, `_2`, etc.
- Example: `Calgary_Budget_2023.pdf` → `Calgary_Budget_2023_1.pdf`

## Performance & Costs

### Text Extraction
- **Speed:** ~0.5-2s per PDF (first 3 pages)
- **Cost:** Free (local processing)

### OpenAI Analysis
- **Model:** gpt-4o-mini
- **Input:** ~2000 chars per PDF
- **Cost:** ~$0.0003 per PDF (very cheap)
- **Speed:** ~1-2s per API call

### Batch Processing
For 100 PDFs:
- **Time:** ~3-5 minutes
- **Cost:** ~$0.03 total

## Best Practices

### 1. Run Dry Run First
```bash
python rename_existing_pdfs.py --dry-run
```
Review proposed changes before committing.

### 2. Keep Metadata
Always use `update_metadata=True` to track rename history.

### 3. Handle Duplicates
The system automatically handles:
- Multiple documents same year (adds suffix)
- Fiscal year ranges (2023-2024)
- Unknown years (uses "Unknown_Year")

### 4. Verify Results
Check `metadata.json` for:
- Confidence levels (high/medium/low)
- Reasoning (explains AI decision)
- Original filename (for rollback if needed)

## Examples

### Example 1: Consolidated Financial Statements
```
Original: acfr-2023.pdf
Renamed:  Toronto_Consolidated_Financial_Statements_2023.pdf
```

### Example 2: Fiscal Year Budget
```
Original: budget_2023-2024.pdf
Renamed:  Calgary_Budget_Document_2023-2024.pdf
```

### Example 3: PAFR (Popular Annual Financial Report)
```
Original: popular-report-2023.pdf
Renamed:  Vancouver_Popular_Annual_Financial_Report_2023.pdf
```

### Example 4: Interim Statements
```
Original: q2-financials-2024.pdf
Renamed:  Montreal_Interim_Financial_Statements_2024.pdf
```

## Integration with Build Canada Portal

This system supports the Build Canada initiative by:

1. **Standardizing Upload Names** - All PDFs have consistent naming for portal upload
2. **Preserving Metadata** - Document type and year tracked for database entry
3. **Enabling Bulk Operations** - Easily identify document types across 3,696 municipalities
4. **Supporting Sankey Diagrams** - Clear document identification helps categorize revenue/spending

## Troubleshooting

### "No text extracted from PDF"
- PDF is likely scanned/image-based
- Consider OCR with pytesseract (not implemented yet)
- Manually rename or skip

### "OpenAI API rate limit"
- Add delay between calls: `time.sleep(1)`
- Reduce batch size
- Check API quota

### "Filename collision"
- System automatically adds suffix
- Check metadata to understand duplicates
- May indicate same document downloaded twice

### "Low confidence rename"
- Review `rename_reasoning` in metadata
- PDF text may be unclear
- Consider manual verification

## Future Enhancements

1. **OCR Support** - Handle scanned PDFs with pytesseract
2. **Batch Rate Limiting** - Built-in rate limiter for large batches
3. **Confidence Threshold** - Skip rename if confidence < threshold
4. **Manual Review Queue** - Flag low-confidence renames for review
5. **Document Type Validation** - Verify document matches expected type
6. **Year Validation** - Warn if year seems incorrect

## Summary

The PDF Intelligent Renaming System transforms chaotic downloaded PDFs into a well-organized, standardized collection suitable for the Build Canada portal. By extracting text and using AI to identify document types and years, it ensures every financial statement across Canada's 3,696 municipalities is properly named and catalogued.

**Key Benefits:**
- ✅ Consistent naming convention
- ✅ Automated text extraction
- ✅ AI-powered document identification  
- ✅ Full metadata tracking
- ✅ Integrated into scraper workflow
- ✅ Post-processing support for existing files
