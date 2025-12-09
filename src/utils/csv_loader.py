"""CSV data loader for municipalities."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from .logger import setup_logger

logger = setup_logger(__name__)


class MunicipalityCSVLoader:
    """Load and manage municipality data from CSV."""
    
    def __init__(self, csv_path: str = "municipalities_clean.csv"):
        """
        Initialize CSV loader.
        
        Args:
            csv_path: Path to CSV file
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.df = pd.read_csv(self.csv_path)
        logger.info(f"Loaded {len(self.df)} municipalities from {csv_path}")
    
    def get_all_municipalities(self) -> List[Dict[str, Any]]:
        """
        Get all municipalities.
        
        Returns:
            List of municipality dictionaries
        """
        return self.df.to_dict('records')
    
    def get_municipality_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get municipality by name.
        
        Args:
            name: Municipality name
        
        Returns:
            Municipality data or None
        """
        result = self.df[self.df['name'].str.lower() == name.lower()]
        if len(result) > 0:
            return result.iloc[0].to_dict()
        return None
    
    def get_top_n_by_population(self, n: int = 50) -> List[Dict[str, Any]]:
        """
        Get top N municipalities by population.
        
        Args:
            n: Number of municipalities to return
        
        Returns:
            List of municipality dictionaries
        """
        sorted_df = self.df.nlargest(n, 'pop')
        return sorted_df.to_dict('records')
    
    def filter_by_province(self, province_code: str) -> List[Dict[str, Any]]:
        """
        Filter municipalities by province.
        
        Args:
            province_code: Province code (e.g., '35' for Ontario, '24' for Quebec)
        
        Returns:
            List of municipality dictionaries
        """
        filtered = self.df[self.df['PR_UID'] == province_code]
        return filtered.to_dict('records')
    
    def get_municipality_search_query(self, municipality: Dict[str, Any]) -> str:
        """
        Generate search query for municipality.
        
        Args:
            municipality: Municipality data dictionary
        
        Returns:
            Search query string
        """
        name = municipality['name']
        region = municipality.get('region', '')
        
        # Handle special cases like "Greater Sudbury / Grand Sudbury"
        if '/' in name:
            name = name.split('/')[0].strip()
        
        return f"{name} previous financial statements"
