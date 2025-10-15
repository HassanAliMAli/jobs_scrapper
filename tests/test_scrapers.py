"""
Unit tests for scrapers
"""

import pytest
import os
from datetime import datetime, date
from scrapers.base import BaseScraper
from scrapers.rozee import RozeeScraper
from scrapers.mustakbil import MustakbilScraper


class TestBaseScraper:
    """Test BaseScraper functionality"""
    
    def test_clean_text(self):
        """Test text cleaning"""
        scraper = RozeeScraper()
        
        # Multiple spaces
        assert scraper.clean_text("Hello    World") == "Hello World"
        
        # Leading/trailing whitespace
        assert scraper.clean_text("  Test  ") == "Test"
        
        # Newlines and tabs
        assert scraper.clean_text("Line1\n\tLine2") == "Line1 Line2"
    
    def test_extract_salary(self):
        """Test salary extraction"""
        scraper = RozeeScraper()
        
        # Standard range
        result = scraper.extract_salary("PKR 50,000 - 80,000")
        assert result['salary_min'] == 50000
        assert result['salary_max'] == 80000
        assert result['salary_currency'] == 'PKR'
        
        # USD
        result = scraper.extract_salary("$1000 - $2000")
        assert result['salary_currency'] == 'USD'
        
        # Single value
        result = scraper.extract_salary("PKR 60,000")
        assert result['salary_min'] == 60000
    
    def test_generate_job_hash(self):
        """Test job hash generation"""
        scraper = RozeeScraper()
        
        url1 = "https://example.com/job1"
        url2 = "https://example.com/job2"
        
        hash1 = scraper.generate_job_hash(url1)
        hash2 = scraper.generate_job_hash(url2)
        
        # Same URL should produce same hash
        assert hash1 == scraper.generate_job_hash(url1)
        
        # Different URLs should produce different hashes
        assert hash1 != hash2


class TestRozeeScraper:
    """Test Rozee.pk scraper"""
    
    def test_initialization(self):
        """Test scraper initialization"""
        scraper = RozeeScraper()
        
        assert scraper.site_name == 'rozee'
        assert 'rozee.pk' in scraper.base_url
        assert scraper.max_pages > 0
    
    def test_parse_date(self):
        """Test date parsing"""
        scraper = RozeeScraper()
        
        # Today
        result = scraper.parse_date("Today")
        assert result == datetime.now().date()
        
        # Days ago
        result = scraper.parse_date("3 days ago")
        assert result <= datetime.now().date()
        
        # Weeks ago
        result = scraper.parse_date("2 weeks ago")
        assert result <= datetime.now().date()


class TestMustakbilScraper:
    """Test Mustakbil.com scraper"""
    
    def test_initialization(self):
        """Test scraper initialization"""
        scraper = MustakbilScraper()
        
        assert scraper.site_name == 'mustakbil'
        assert 'mustakbil.com' in scraper.base_url


@pytest.mark.integration
class TestScraperIntegration:
    """Integration tests - requires database connection"""
    
    @pytest.fixture
    def db_url(self):
        """Get test database URL"""
        return os.getenv('DATABASE_URL')
    
    def test_database_connection(self, db_url):
        """Test database connection"""
        if not db_url:
            pytest.skip("DATABASE_URL not set")
        
        scraper = RozeeScraper()
        scraper.connect_db()
        
        assert scraper.conn is not None
        assert scraper.cursor is not None
        
        scraper.close_db()
