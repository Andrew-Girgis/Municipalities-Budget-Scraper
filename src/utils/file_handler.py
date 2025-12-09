"""File handling utilities for downloading and managing documents."""
import os
import json
import re
import requests
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse, urljoin
from .logger import setup_logger

logger = setup_logger(__name__)


class FileHandler:
    """Handles file operations for downloading and organizing documents."""
    
    def __init__(self, base_data_dir: str = "data"):
        """
        Initialize file handler.
        
        Args:
            base_data_dir: Base directory for storing data
        """
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)
        logger.info(f"FileHandler initialized with base directory: {self.base_data_dir}")
    
    def get_municipality_dir(self, municipality_name: str) -> Path:
        """
        Get or create directory for a municipality.
        
        Args:
            municipality_name: Name of the municipality
        
        Returns:
            Path to municipality directory
        """
        muni_dir = self.base_data_dir / municipality_name
        muni_dir.mkdir(exist_ok=True)
        return muni_dir
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to be filesystem-safe.
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        return filename
    
    def municipality_folder_exists(self, municipality_name: str) -> bool:
        """
        Check if municipality folder exists.
        
        Args:
            municipality_name: Name of the municipality
        
        Returns:
            True if folder exists, False otherwise
        """
        muni_dir = self.base_data_dir / municipality_name
        return muni_dir.exists()
    
    def get_existing_pdfs(self, municipality_name: str) -> list:
        """
        Get list of existing PDFs in municipality folder.
        
        Args:
            municipality_name: Name of the municipality
        
        Returns:
            List of PDF file paths
        """
        muni_dir = self.base_data_dir / municipality_name
        if not muni_dir.exists():
            return []
        return list(muni_dir.glob('*.pdf'))
    
    def download_pdf(
        self,
        url: str,
        municipality_name: str,
        year: Optional[int] = None,
        custom_filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Download a PDF file.
        
        Args:
            url: URL of the PDF
            municipality_name: Municipality name
            year: Year of the document
            custom_filename: Custom filename (if not provided, extracts from URL)
        
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Get municipality directory
            muni_dir = self.get_municipality_dir(municipality_name)
            
            # Determine filename
            if custom_filename:
                filename = self.sanitize_filename(custom_filename)
            else:
                # Extract filename from URL
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                
                # If no filename in URL, generate one
                if not filename or not filename.endswith('.pdf'):
                    year_str = f"{year}_" if year else ""
                    filename = f"{year_str}financial_report.pdf"
                
                filename = self.sanitize_filename(filename)
            
            # Ensure .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            filepath = muni_dir / filename
            
            # Check if file already exists
            if filepath.exists():
                logger.info(f"File already exists: {filepath}")
                return filepath
            
            # Download the file
            logger.info(f"Downloading {url} to {filepath}")
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Verify it's a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                logger.warning(f"URL may not be a PDF (content-type: {content_type}): {url}")
            
            # Write file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded: {filepath}")
            return filepath
            
        except requests.Timeout:
            logger.warning(f"Timeout downloading {url}")
            return None
        except requests.HTTPError as e:
            logger.error(f"HTTP error downloading {url}: {e.response.status_code}")
            return None
        except requests.ConnectionError:
            logger.error(f"Connection error downloading {url}")
            return None
        except Exception:
            logger.exception(f"Unexpected error downloading {url}")
            return None
    
    def save_metadata(
        self,
        municipality_name: str,
        filename: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Save metadata for a downloaded document.
        
        Args:
            municipality_name: Municipality name
            filename: Filename of the document
            metadata: Metadata dictionary
        """
        try:
            muni_dir = self.get_municipality_dir(municipality_name)
            metadata_file = muni_dir / "metadata.json"
            
            # Load existing metadata
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    all_metadata = json.load(f)
            else:
                all_metadata = {}
            
            # Add timestamp
            metadata['download_timestamp'] = datetime.now().isoformat()
            
            # Update metadata
            all_metadata[filename] = metadata
            
            # Save updated metadata
            with open(metadata_file, 'w') as f:
                json.dump(all_metadata, f, indent=2)
            
            logger.debug(f"Saved metadata for {filename}")
            
        except Exception:
            logger.exception(f"Error saving metadata for {filename}")
    
    def get_metadata(self, municipality_name: str) -> Dict[str, Any]:
        """
        Get all metadata for a municipality.
        
        Args:
            municipality_name: Municipality name
        
        Returns:
            Metadata dictionary
        """
        try:
            muni_dir = self.get_municipality_dir(municipality_name)
            metadata_file = muni_dir / "metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            return {}
            
        except Exception:
            logger.exception(f"Error loading metadata for {municipality_name}")
            return {}
    
    def file_exists(self, municipality_name: str, filename: str) -> bool:
        """
        Check if a file already exists.
        
        Args:
            municipality_name: Municipality name
            filename: Filename to check
        
        Returns:
            True if file exists, False otherwise
        """
        muni_dir = self.get_municipality_dir(municipality_name)
        filepath = muni_dir / filename
        return filepath.exists()
    
    def rename_pdf_with_extracted_info(
        self,
        municipality_name: str,
        current_filename: str,
        pdf_text: str,
        openai_client,
        update_metadata: bool = True
    ) -> Optional[Path]:
        """
        Rename a PDF file using extracted text and OpenAI analysis.
        
        Args:
            municipality_name: Municipality name
            current_filename: Current filename of the PDF
            pdf_text: Extracted text from PDF
            openai_client: OpenAIClient instance for analysis
            update_metadata: Whether to update metadata.json with rename info
        
        Returns:
            Path to renamed file or None if failed
        """
        try:
            muni_dir = self.get_municipality_dir(municipality_name)
            current_path = muni_dir / current_filename
            
            if not current_path.exists():
                logger.error(f"File not found: {current_path}")
                return None
            
            # Generate standardized filename using OpenAI
            logger.info(f"Analyzing {current_filename} for intelligent renaming...")
            result = openai_client.generate_standardized_filename(
                pdf_text=pdf_text,
                csd_name=municipality_name,
                current_filename=current_filename
            )
            
            new_filename = result['filename']
            new_path = muni_dir / new_filename
            
            # Check if filename would be the same
            if current_path == new_path:
                logger.info(f"Filename already standardized: {current_filename}")
                return current_path
            
            # Check if target filename already exists
            if new_path.exists():
                logger.warning(f"Target filename already exists: {new_filename}")
                # Add suffix to avoid collision
                base_name = new_filename.rsplit('.pdf', 1)[0]
                counter = 1
                while new_path.exists():
                    new_filename = f"{base_name}_{counter}.pdf"
                    new_path = muni_dir / new_filename
                    counter += 1
                logger.info(f"Using unique filename: {new_filename}")
            
            # Rename the file
            current_path.rename(new_path)
            logger.info(f"Renamed: {current_filename} -> {new_filename}")
            
            # Update metadata if requested
            if update_metadata:
                metadata = self.get_metadata(municipality_name)
                
                # Move metadata from old filename to new filename
                if current_filename in metadata:
                    file_metadata = metadata.pop(current_filename)
                else:
                    file_metadata = {}
                
                # Add rename information
                file_metadata['original_filename'] = current_filename
                file_metadata['standardized_filename'] = new_filename
                file_metadata['document_type'] = result['document_type']
                file_metadata['document_year'] = result['year']
                file_metadata['rename_confidence'] = result['confidence']
                file_metadata['rename_reasoning'] = result['reasoning']
                file_metadata['renamed_at'] = datetime.now().isoformat()
                
                # Save updated metadata under new filename
                metadata[new_filename] = file_metadata
                
                metadata_file = muni_dir / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.debug(f"Updated metadata for {new_filename}")
            
            return new_path
            
        except Exception:
            logger.exception(f"Error renaming PDF {current_filename} with extracted info")
            return None

    def rename_pdf_with_extracted_info(
        self,
        municipality_name: str,
        current_filename: str,
        pdf_text: str,
        openai_client,
        update_metadata: bool = True
    ) -> Optional[Path]:
        """
        Rename a PDF file using extracted text and OpenAI analysis.
        
        Args:
            municipality_name: Municipality name
            current_filename: Current filename of the PDF
            pdf_text: Extracted text from PDF
            openai_client: OpenAIClient instance for analysis
            update_metadata: Whether to update metadata.json with rename info
        
        Returns:
            Path to renamed file or None if failed
        """
        try:
            muni_dir = self.get_municipality_dir(municipality_name)
            current_path = muni_dir / current_filename
            
            if not current_path.exists():
                logger.error(f"File not found: {current_path}")
                return None
            
            # Generate standardized filename using OpenAI
            logger.info(f"Analyzing {current_filename} for intelligent renaming...")
            result = openai_client.generate_standardized_filename(
                pdf_text=pdf_text,
                csd_name=municipality_name,
                current_filename=current_filename
            )
            
            new_filename = result['filename']
            new_path = muni_dir / new_filename
            
            # Check if filename would be the same
            if current_path == new_path:
                logger.info(f"Filename already standardized: {current_filename}")
                return current_path
            
            # Check if target filename already exists
            if new_path.exists():
                logger.warning(f"Target filename already exists: {new_filename}")
                # Add suffix to avoid collision
                base_name = new_filename.rsplit('.pdf', 1)[0]
                counter = 1
                while new_path.exists():
                    new_filename = f"{base_name}_{counter}.pdf"
                    new_path = muni_dir / new_filename
                    counter += 1
                logger.info(f"Using unique filename: {new_filename}")
            
            # Rename the file
            current_path.rename(new_path)
            logger.info(f"Renamed: {current_filename} -> {new_filename}")
            
            # Update metadata if requested
            if update_metadata:
                metadata = self.get_metadata(municipality_name)
                
                # Move metadata from old filename to new filename
                if current_filename in metadata:
                    file_metadata = metadata.pop(current_filename)
                else:
                    file_metadata = {}
                
                # Add rename information
                file_metadata['original_filename'] = current_filename
                file_metadata['standardized_filename'] = new_filename
                file_metadata['document_type'] = result['document_type']
                file_metadata['document_year'] = result['year']
                file_metadata['rename_confidence'] = result['confidence']
                file_metadata['rename_reasoning'] = result['reasoning']
                file_metadata['renamed_at'] = datetime.now().isoformat()
                
                # Save updated metadata under new filename
                metadata[new_filename] = file_metadata
                
                metadata_file = muni_dir / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.debug(f"Updated metadata for {new_filename}")
            
            return new_path
            
        except Exception:
            logger.exception(f"Error renaming PDF {current_filename} in duplicate method")
            return None
