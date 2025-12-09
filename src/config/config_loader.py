"""Configuration loader for municipalities."""
import yaml
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class YearRange(BaseModel):
    """Year range configuration."""
    start: int
    end: int


class MunicipalityConfig(BaseModel):
    """Configuration for a single municipality."""
    name: str
    website: str
    search_paths: List[str] = Field(default_factory=list)
    document_patterns: List[str] = Field(default_factory=list)
    year_range: YearRange


class Config(BaseModel):
    """Main configuration."""
    municipalities: List[MunicipalityConfig]


def load_config(config_path: str = "municipalities.yaml") -> Config:
    """
    Load municipalities configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Config object
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    return Config(**config_data)


def get_municipality_config(municipality_name: str, config_path: str = "municipalities.yaml") -> MunicipalityConfig:
    """
    Get configuration for a specific municipality.
    
    Args:
        municipality_name: Name of the municipality
        config_path: Path to configuration file
    
    Returns:
        Municipality configuration
    
    Raises:
        ValueError: If municipality not found in config
    """
    config = load_config(config_path)
    
    for muni in config.municipalities:
        if muni.name.lower() == municipality_name.lower():
            return muni
    
    raise ValueError(f"Municipality '{municipality_name}' not found in configuration")
