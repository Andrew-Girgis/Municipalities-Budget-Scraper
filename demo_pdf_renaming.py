#!/usr/bin/env python3
"""
Demo script to showcase PDF intelligent renaming capabilities.

This demonstrates the complete workflow:
1. Extract text from PDF
2. Analyze with OpenAI
3. Generate standardized filename
4. Show metadata
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import PDFTextExtractor, OpenAIClient, setup_logger

logger = setup_logger(__name__)


def demo_text_extraction():
    """Demo: Extract text from a PDF."""
    print("\n" + "="*80)
    print("DEMO 1: PDF Text Extraction")
    print("="*80)
    
    extractor = PDFTextExtractor()
    
    # Find a sample PDF
    data_dir = Path("data")
    sample_pdf = None
    
    for muni_dir in data_dir.iterdir():
        if muni_dir.is_dir():
            pdfs = list(muni_dir.glob("*.pdf"))
            if pdfs:
                sample_pdf = pdfs[0]
                break
    
    if not sample_pdf:
        print("❌ No PDFs found in data/ directory")
        print("   Run the scraper first: python scrape_with_playwright.py --municipality Calgary")
        return
    
    print(f"\n📄 Sample PDF: {sample_pdf.name}")
    print(f"   Location: {sample_pdf}")
    
    # Check if text-based
    is_text = extractor.is_text_based_pdf(sample_pdf)
    print(f"\n✓ Text-based PDF: {is_text}")
    
    if is_text:
        # Extract text
        text = extractor.extract_text_from_pdf(sample_pdf, max_chars=500)
        print(f"\n✓ Extracted {len(text)} characters")
        print("\n--- First 500 chars ---")
        print(text)
        print("--- End excerpt ---")
    else:
        print("⚠️  PDF appears to be scanned/image-based")


def demo_intelligent_naming():
    """Demo: Generate standardized filename."""
    print("\n" + "="*80)
    print("DEMO 2: Intelligent Filename Generation")
    print("="*80)
    
    extractor = PDFTextExtractor()
    openai = OpenAIClient()
    
    # Find a sample PDF
    data_dir = Path("data")
    sample_pdf = None
    municipality_name = None
    
    for muni_dir in data_dir.iterdir():
        if muni_dir.is_dir():
            pdfs = list(muni_dir.glob("*.pdf"))
            if pdfs:
                sample_pdf = pdfs[0]
                municipality_name = muni_dir.name
                break
    
    if not sample_pdf:
        print("❌ No PDFs found in data/ directory")
        return
    
    print(f"\n📄 Analyzing: {sample_pdf.name}")
    print(f"   Municipality: {municipality_name}")
    
    # Extract text
    print("\n⏳ Extracting text from PDF...")
    text = extractor.extract_text_from_pdf(sample_pdf, max_chars=2000)
    
    if not text:
        print("❌ Could not extract text from PDF")
        return
    
    print(f"✓ Extracted {len(text)} characters")
    
    # Generate standardized filename
    print("\n⏳ Analyzing with OpenAI...")
    result = openai.generate_standardized_filename(
        pdf_text=text,
        csd_name=municipality_name,
        current_filename=sample_pdf.name
    )
    
    print("\n" + "-"*80)
    print("RESULTS:")
    print("-"*80)
    print(f"Original filename:   {sample_pdf.name}")
    print(f"Standardized name:   {result['filename']}")
    print(f"Document type:       {result['document_type']}")
    print(f"Year:                {result['year']}")
    print(f"Confidence:          {result['confidence']}")
    print(f"\nReasoning:")
    print(f"  {result['reasoning']}")
    print("-"*80)


def demo_complete_workflow():
    """Demo: Complete rename workflow."""
    print("\n" + "="*80)
    print("DEMO 3: Complete Rename Workflow (DRY RUN)")
    print("="*80)
    
    from src.utils import FileHandler
    
    extractor = PDFTextExtractor()
    openai = OpenAIClient()
    file_handler = FileHandler()
    
    # Find a sample PDF
    data_dir = Path("data")
    sample_pdf = None
    municipality_name = None
    
    for muni_dir in data_dir.iterdir():
        if muni_dir.is_dir():
            pdfs = list(muni_dir.glob("*.pdf"))
            if pdfs:
                sample_pdf = pdfs[0]
                municipality_name = muni_dir.name
                break
    
    if not sample_pdf:
        print("❌ No PDFs found in data/ directory")
        return
    
    print(f"\n📄 Processing: {sample_pdf.name}")
    print(f"   Municipality: {municipality_name}")
    
    # Extract text
    print("\n[1/4] Extracting text...")
    text = extractor.extract_text_from_pdf(sample_pdf, max_chars=2000)
    
    if not text:
        print("❌ Could not extract text")
        return
    
    print(f"✓ Extracted {len(text)} characters")
    
    # Analyze
    print("\n[2/4] Analyzing with OpenAI...")
    result = openai.generate_standardized_filename(
        pdf_text=text,
        csd_name=municipality_name,
        current_filename=sample_pdf.name
    )
    print(f"✓ Generated: {result['filename']}")
    
    # Show what would happen
    print("\n[3/4] Rename operation (DRY RUN):")
    print(f"    FROM: {sample_pdf.name}")
    print(f"    TO:   {result['filename']}")
    
    print("\n[4/4] Metadata update:")
    print("    Would add to metadata.json:")
    print(f"      - original_filename: {sample_pdf.name}")
    print(f"      - standardized_filename: {result['filename']}")
    print(f"      - document_type: {result['document_type']}")
    print(f"      - document_year: {result['year']}")
    print(f"      - rename_confidence: {result['confidence']}")
    
    print("\n✓ Workflow complete (no files modified in demo)")


def main():
    """Run all demos."""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "PDF INTELLIGENT RENAMING DEMO" + " "*28 + "║")
    print("╚" + "="*78 + "╝")
    
    try:
        demo_text_extraction()
        demo_intelligent_naming()
        demo_complete_workflow()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE")
        print("="*80)
        print("\nTo rename existing PDFs:")
        print("  python rename_existing_pdfs.py --dry-run")
        print("\nTo enable auto-rename in scraper:")
        print("  python scrape_with_playwright.py --municipality Calgary")
        print("\n" + "="*80)
        
    except Exception as e:
        logger.error(f"Error running demo: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Installed dependencies: pip install -r requirements.txt")
        print("  2. Set OPENAI_API_KEY in .env")
        print("  3. Downloaded some PDFs first")


if __name__ == "__main__":
    main()
