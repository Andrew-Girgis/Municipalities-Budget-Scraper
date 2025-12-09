"""Scraper modules initialization."""
from .municipality_scraper import MunicipalityScraper
from .playwright_municipality_scraper import PlaywrightMunicipalityScraper

__all__ = ['MunicipalityScraper', 'PlaywrightMunicipalityScraper']
