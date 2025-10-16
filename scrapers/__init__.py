"""
Scrapers package - Currently supports Rozee.pk
"""

from .base import BaseScraper
from .rozee import RozeeScraper

__all__ = ['BaseScraper', 'RozeeScraper']

SCRAPERS = {'rozee': RozeeScraper}
