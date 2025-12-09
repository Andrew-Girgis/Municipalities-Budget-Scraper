#!/usr/bin/env python3
"""
Utility script to view and manage downloaded municipality data.

Usage:
    python view_data.py                    # List all downloaded documents
    python view_data.py --municipality Toronto  # List Toronto's documents
    python view_data.py --stats            # Show statistics
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from src.utils import setup_logger

logger = setup_logger("view_data", log_level="INFO")


def list_municipality_files(municipality_name: str, data_dir: Path = Path("data")) -> None:
    """List all files for a municipality."""
    muni_dir = data_dir / municipality_name
    
    if not muni_dir.exists():
        logger.warning(f"No data directory found for {municipality_name}")
        return
    
    # Load metadata
    metadata_file = muni_dir / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    
    # List PDF files
    pdf_files = sorted(muni_dir.glob("*.pdf"))
    
    print(f"\n{'='*70}")
    print(f"{municipality_name}")
    print(f"{'='*70}")
    print(f"Directory: {muni_dir}")
    print(f"Total PDFs: {len(pdf_files)}\n")
    
    if not pdf_files:
        print("No PDF files found.")
        return
    
    for pdf_file in pdf_files:
        file_metadata = metadata.get(pdf_file.name, {})
        
        # Get file info
        file_size = pdf_file.stat().st_size / (1024 * 1024)  # MB
        year = file_metadata.get('year', 'Unknown')
        doc_type = file_metadata.get('document_type', 'Unknown')
        source_url = file_metadata.get('source_url', 'N/A')
        
        print(f"📄 {pdf_file.name}")
        print(f"   Year: {year}")
        print(f"   Type: {doc_type}")
        print(f"   Size: {file_size:.2f} MB")
        if source_url != 'N/A':
            print(f"   Source: {source_url}")
        print()


def show_statistics(data_dir: Path = Path("data")) -> None:
    """Show overall statistics."""
    if not data_dir.exists():
        logger.warning("No data directory found")
        return
    
    municipalities = [d for d in data_dir.iterdir() if d.is_dir()]
    
    total_pdfs = 0
    total_size = 0
    year_stats = defaultdict(int)
    municipality_stats = {}
    
    print(f"\n{'='*70}")
    print("OVERALL STATISTICS")
    print(f"{'='*70}\n")
    
    for muni_dir in municipalities:
        muni_name = muni_dir.name
        
        # Count PDFs
        pdf_files = list(muni_dir.glob("*.pdf"))
        pdf_count = len(pdf_files)
        total_pdfs += pdf_count
        
        # Calculate size
        muni_size = sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)  # MB
        total_size += muni_size
        
        # Load metadata for year stats
        metadata_file = muni_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                for file_meta in metadata.values():
                    year = file_meta.get('year', 'Unknown')
                    if year != 'Unknown':
                        year_stats[str(year)] += 1
        
        municipality_stats[muni_name] = {
            'count': pdf_count,
            'size': muni_size
        }
    
    # Print municipality stats
    print("By Municipality:")
    for muni_name in sorted(municipality_stats.keys()):
        stats = municipality_stats[muni_name]
        print(f"  {muni_name:20} {stats['count']:3d} documents ({stats['size']:7.2f} MB)")
    
    print(f"\n{'─'*70}")
    print(f"  {'Total':20} {total_pdfs:3d} documents ({total_size:7.2f} MB)")
    
    # Print year coverage
    if year_stats:
        print(f"\nYear Coverage:")
        for year in sorted(year_stats.keys()):
            count = year_stats[year]
            print(f"  {year}: {count} document(s)")
    
    print(f"\n{'='*70}\n")


def list_all_municipalities(data_dir: Path = Path("data")) -> None:
    """List all municipalities with data."""
    if not data_dir.exists():
        logger.warning("No data directory found")
        return
    
    municipalities = sorted([d for d in data_dir.iterdir() if d.is_dir()], key=lambda x: x.name)
    
    print(f"\n{'='*70}")
    print("ALL MUNICIPALITIES")
    print(f"{'='*70}\n")
    
    if not municipalities:
        print("No municipality data found.")
        return
    
    for muni_dir in municipalities:
        pdf_count = len(list(muni_dir.glob("*.pdf")))
        print(f"  • {muni_dir.name:20} ({pdf_count} document(s))")
    
    print(f"\n{'='*70}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View and manage downloaded municipality data"
    )
    
    parser.add_argument(
        '--municipality',
        '-m',
        type=str,
        help='View files for specific municipality'
    )
    
    parser.add_argument(
        '--stats',
        '-s',
        action='store_true',
        help='Show statistics'
    )
    
    parser.add_argument(
        '--data-dir',
        '-d',
        type=str,
        default='data',
        help='Path to data directory (default: data)'
    )
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    
    if args.stats:
        show_statistics(data_dir)
    elif args.municipality:
        list_municipality_files(args.municipality, data_dir)
    else:
        list_all_municipalities(data_dir)


if __name__ == "__main__":
    main()
