"""URL cache manager for storing discovered links and PDFs."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .logger import setup_logger

logger = setup_logger(__name__)


class URLCache:
    """Manages caching of discovered URLs and PDFs for municipalities."""
    
    def __init__(self, cache_file: str = "url_cache.json"):
        """
        Initialize URL cache.
        
        Args:
            cache_file: Path to cache JSON file
        """
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        logger.info(f"URL cache initialized: {self.cache_file}")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from JSON file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded cache with {len(cache)} municipalities")
                return cache
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to JSON file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.info(f"Cache saved: {len(self.cache)} municipalities")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def get_municipality_data(self, csd_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data for a municipality.
        
        Args:
            csd_name: Municipality name
        
        Returns:
            Cached data or None if not found
        """
        return self.cache.get(csd_name)
    
    def has_municipality(self, csd_name: str) -> bool:
        """Check if municipality is in cache."""
        return csd_name in self.cache
    
    def update_municipality(
        self,
        csd_name: str,
        parent_link: str,
        financial_documents: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update or create municipality entry in cache.
        
        Args:
            csd_name: Municipality name
            parent_link: Main financial reports page URL
            financial_documents: Dict mapping year/doc_type to PDF URL
            metadata: Optional metadata (discovery date, etc.)
        """
        entry = {
            'CSD': csd_name,
            'parent_link': parent_link,
            'financial_documents': financial_documents,
            'last_updated': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.cache[csd_name] = entry
        self._save_cache()
        logger.info(f"Updated cache for {csd_name}: {len(financial_documents)} documents")
    
    def add_document(self, csd_name: str, year: str, pdf_url: str, parent_link: str = None):
        """
        Add a single document to municipality's cache.
        
        Args:
            csd_name: Municipality name
            year: Document year or identifier
            pdf_url: PDF URL
            parent_link: Parent page URL (if new municipality)
        """
        if csd_name not in self.cache:
            self.cache[csd_name] = {
                'CSD': csd_name,
                'parent_link': parent_link or '',
                'financial_documents': {},
                'last_updated': datetime.now().isoformat(),
                'metadata': {}
            }
        
        self.cache[csd_name]['financial_documents'][year] = pdf_url
        self.cache[csd_name]['last_updated'] = datetime.now().isoformat()
        self._save_cache()
        logger.debug(f"Added document to {csd_name}: {year} -> {pdf_url}")
    
    def get_documents(self, csd_name: str) -> Dict[str, str]:
        """
        Get all documents for a municipality.
        
        Args:
            csd_name: Municipality name
        
        Returns:
            Dictionary mapping year/doc_type to PDF URL
        """
        if csd_name in self.cache:
            return self.cache[csd_name].get('financial_documents', {})
        return {}
    
    def get_parent_link(self, csd_name: str) -> Optional[str]:
        """Get parent link for municipality."""
        if csd_name in self.cache:
            return self.cache[csd_name].get('parent_link')
        return None
    
    def remove_municipality(self, csd_name: str):
        """Remove municipality from cache."""
        if csd_name in self.cache:
            del self.cache[csd_name]
            self._save_cache()
            logger.info(f"Removed {csd_name} from cache")
    
    def get_all_municipalities(self) -> List[str]:
        """Get list of all cached municipalities."""
        return list(self.cache.keys())
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_munis = len(self.cache)
        total_docs = sum(len(m.get('financial_documents', {})) for m in self.cache.values())
        
        return {
            'total_municipalities': total_munis,
            'total_documents': total_docs,
            'average_docs_per_municipality': total_docs / total_munis if total_munis > 0 else 0
        }
