"""
Scrapers package for PakJobs Aggregator
Contains base scraper class and site-specific implementations
"""

from .base import BaseScraper
from .rozee import RozeeScraper
from .mustakbil import MustakbilScraper
from .indeed import IndeedScraper
from .brightspyre import BrightSpyreScraper
from .bayt import BaytScraper
from .jobz import JobzScraper
from .bayrozgar import BayrozgarScraper
from .jobsalert import JobsAlertScraper
from .pakpositions import PakPositionsScraper

__all__ = [
    'BaseScraper',
    'RozeeScraper',
    'MustakbilScraper',
    'IndeedScraper',
    'BrightSpyreScraper',
    'BaytScraper',
    'JobzScraper',
    'BayrozgarScraper',
    'JobsAlertScraper',
    'PakPositionsScraper',
]

# Scraper registry for easy access
SCRAPERS = {
    'rozee': RozeeScraper,
    'mustakbil': MustakbilScraper,
    'indeed': IndeedScraper,
    'brightspyre': BrightSpyreScraper,
    'bayt': BaytScraper,
    'jobz': JobzScraper,
    'bayrozgar': BayrozgarScraper,
    'jobsalert': JobsAlertScraper,
    'pakpositions': PakPositionsScraper,
}
