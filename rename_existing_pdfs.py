#!/usr/bin/env python3
"""
Post-processing script to rename existing PDFs using intelligent text extraction.

This script:
1. Scans all municipality folders in data/
2. Extracts text from each PDF
3. Uses OpenAI to generate standardized filenames
4. Renames PDFs to follow pattern: {CSD_Name}_{Document_Type}_{Year}.pdf
5. Updates metadata.json with rename information
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import (
    setup_logger,
    FileHandler,
    OpenAIClient,
    PDFTextExtractor
)

logger = setup_logger(__name__)


class PDFRenamer:
    """Handles batch renaming of PDFs."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize PDF renamer.
        
        Args:
            data_dir: Base data directory containing municipality folders
        """
        self.data_dir = Path(data_dir)
        self.file_handler = FileHandler(base_data_dir=str(data_dir))
        self.openai_client = OpenAIClient()
        self.pdf_extractor = PDFTextExtractor()
        
        self.stats = {
            'total_pdfs': 0,
            'renamed': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }
    
    def get_all_municipalities(self) -> List[str]:
        """
        Get list of all municipality folders.
        
        Returns:
            List of municipality names
        """
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return []
        
        municipalities = [
            d.name for d in self.data_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]
        
        logger.info(f"Found {len(municipalities)} municipality folders")
        return municipalities
    
    def get_pdfs_for_municipality(self, municipality_name: str) -> List[Path]:
        """
        Get all PDF files for a municipality.
        
        Args:
            municipality_name: Municipality name
        
        Returns:
            List of PDF file paths
        """
        muni_dir = self.data_dir / municipality_name
        if not muni_dir.exists():
            return []
        
        pdfs = list(muni_dir.glob('*.pdf'))
        logger.debug(f"Found {len(pdfs)} PDFs in {municipality_name}")
        return pdfs
    
    def process_pdf(
        self,
        pdf_path: Path,
        municipality_name: str,
        dry_run: bool = False
    ) -> bool:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            municipality_name: Municipality name
            dry_run: If True, don't actually rename files
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.stats['total_pdfs'] += 1
            filename = pdf_path.name
            
            logger.info(f"Processing: {filename}")
            
            # Check if already standardized (contains municipality name)
            if municipality_name.replace(' ', '_') in filename:
                logger.info(f"Skipping (already standardized): {filename}")
                self.stats['skipped'] += 1
                return True
            
            # Extract text from PDF
            pdf_text = self.pdf_extractor.extract_text_from_pdf(pdf_path, max_chars=2000)
            
            if not pdf_text:
                logger.warning(f"No text extracted from {filename} - may be scanned/image-based")
                self.stats['skipped'] += 1
                return False
            
            logger.debug(f"Extracted {len(pdf_text)} chars from {filename}")
            
            if dry_run:
                # Just analyze, don't rename
                result = self.openai_client.generate_standardized_filename(
                    pdf_text=pdf_text,
                    csd_name=municipality_name,
                    current_filename=filename
                )
                logger.info(f"[DRY RUN] Would rename to: {result['filename']}")
                logger.info(f"  Document Type: {result['document_type']}")
                logger.info(f"  Year: {result['year']}")
                logger.info(f"  Confidence: {result['confidence']}")
                self.stats['renamed'] += 1
                return True
            
            # Rename the file
            new_path = self.file_handler.rename_pdf_with_extracted_info(
                municipality_name=municipality_name,
                current_filename=filename,
                pdf_text=pdf_text,
                openai_client=self.openai_client,
                update_metadata=True
            )
            
            if new_path:
                self.stats['renamed'] += 1
                return True
            else:
                self.stats['failed'] += 1
                return False
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {str(e)}")
            self.stats['failed'] += 1
            self.stats['errors'].append({
                'file': str(pdf_path),
                'error': str(e)
            })
            return False
    
    def process_municipality(
        self,
        municipality_name: str,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Process all PDFs for a municipality.
        
        Args:
            municipality_name: Municipality name
            dry_run: If True, don't actually rename files
        
        Returns:
            Statistics dictionary
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {municipality_name}")
        logger.info(f"{'='*80}")
        
        pdfs = self.get_pdfs_for_municipality(municipality_name)
        
        if not pdfs:
            logger.info(f"No PDFs found for {municipality_name}")
            return {'processed': 0, 'renamed': 0, 'failed': 0}
        
        results = {
            'processed': 0,
            'renamed': 0,
            'failed': 0
        }
        
        for pdf_path in pdfs:
            success = self.process_pdf(pdf_path, municipality_name, dry_run)
            results['processed'] += 1
            if success:
                results['renamed'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f"Municipality {municipality_name} - Processed: {results['processed']}, "
                   f"Renamed: {results['renamed']}, Failed: {results['failed']}")
        
        return results
    
    def process_all_municipalities(self, dry_run: bool = False) -> None:
        """
        Process all municipalities.
        
        Args:
            dry_run: If True, don't actually rename files
        """
        municipalities = self.get_all_municipalities()
        
        if not municipalities:
            logger.error("No municipalities found to process")
            return
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Starting batch PDF renaming")
        logger.info(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will rename files)'}")
        logger.info(f"Municipalities: {len(municipalities)}")
        logger.info(f"{'='*80}\n")
        
        for municipality in municipalities:
            self.process_municipality(municipality, dry_run)
        
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print summary statistics."""
        logger.info(f"\n{'='*80}")
        logger.info("SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total PDFs processed: {self.stats['total_pdfs']}")
        logger.info(f"Successfully renamed: {self.stats['renamed']}")
        logger.info(f"Skipped (already standardized): {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        if self.stats['errors']:
            logger.info(f"\nErrors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                logger.info(f"  - {error['file']}: {error['error']}")
            if len(self.stats['errors']) > 10:
                logger.info(f"  ... and {len(self.stats['errors']) - 10} more errors")
        
        logger.info(f"{'='*80}\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Rename existing PDFs using intelligent text extraction'
    )
    parser.add_argument(
        '--municipality',
        '-m',
        type=str,
        help='Process specific municipality only'
    )
    parser.add_argument(
        '--dry-run',
        '-d',
        action='store_true',
        help='Dry run - analyze but don\'t rename files'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Data directory (default: data)'
    )
    
    args = parser.parse_args()
    
    # Create renamer
    renamer = PDFRenamer(data_dir=args.data_dir)
    
    if args.municipality:
        # Process single municipality
        renamer.process_municipality(args.municipality, dry_run=args.dry_run)
        renamer.print_summary()
    else:
        # Process all municipalities
        renamer.process_all_municipalities(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
