"""Configuration module initialization."""
from .config_loader import (
    Config,
    MunicipalityConfig,
    YearRange,
    load_config,
    get_municipality_config
)

__all__ = [
    'Config',
    'MunicipalityConfig',
    'YearRange',
    'load_config',
    'get_municipality_config'
]
