"""
Base scraper class providing common functionality for all job site scrapers
"""

import os
import time
import logging
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseScraper(ABC):
    """
    Abstract base class for all job scrapers
    Provides common functionality: database connection, HTTP requests, logging, etc.
    """
    
    def __init__(self, site_name: str, base_url: str):
        """
        Initialize base scraper
        
        Args:
            site_name: Name of the job site (e.g., 'rozee', 'mustakbil')
            base_url: Base URL of the site
        """
        self.site_name = site_name
        self.base_url = base_url
        self.logger = logging.getLogger(f'scraper.{site_name}')
        
        # Configuration from environment
        self.user_agent = os.getenv('USER_AGENT', 'Mozilla/5.0 (compatible; PakJobsBot/1.0)')
        self.scrape_delay = int(os.getenv('SCRAPE_DELAY_SECONDS', '3'))
        self.max_pages = int(os.getenv('MAX_SCRAPE_PAGES', '50'))
        self.database_url = os.getenv('DATABASE_URL')
        
        # Scraping statistics
        self.stats = {
            'jobs_found': 0,
            'jobs_new': 0,
            'jobs_updated': 0,
            'jobs_skipped': 0,
            'errors': 0,
        }
        
        # Database connection
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.cursor = self.conn.cursor()
            self.logger.info(f"Database connected for {self.site_name}")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    def close_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.logger.info(f"Database connection closed for {self.site_name}")
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with error handling and rate limiting
        
        Args:
            url: URL to request
            method: HTTP method (GET/POST)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object or None if failed
        """
        headers = kwargs.get('headers', {})
        headers['User-Agent'] = self.user_agent
        kwargs['headers'] = headers
        
        try:
            # Rate limiting
            time.sleep(self.scrape_delay)
            
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            
            self.logger.debug(f"Successfully fetched: {url}")
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            self.stats['errors'] += 1
            return None
    
    def parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """
        Parse HTML content with BeautifulSoup
        
        Args:
            html: HTML string
            
        Returns:
            BeautifulSoup object or None
        """
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            self.logger.error(f"HTML parsing failed: {e}")
            return None
    
    def generate_job_hash(self, source_url: str) -> str:
        """
        Generate unique hash for job based on source URL
        
        Args:
            source_url: Original job posting URL
            
        Returns:
            SHA-256 hash string
        """
        return hashlib.sha256(source_url.encode()).hexdigest()
    
    def job_exists(self, source_url: str) -> bool:
        """
        Check if job already exists in database
        
        Args:
            source_url: Job URL to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            self.cursor.execute(
                "SELECT id FROM jobs WHERE source_url = %s",
                (source_url,)
            )
            return self.cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error checking job existence: {e}")
            return False
    
    def insert_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Insert new job into database
        
        Args:
            job_data: Dictionary with job fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Required fields
            required_fields = ['site_source', 'source_url', 'title', 'company']
            for field in required_fields:
                if field not in job_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Set defaults
            job_data.setdefault('posted_date', datetime.now().date())
            job_data.setdefault('is_active', True)
            job_data.setdefault('country', 'Pakistan')
            
            # Convert skills list to JSONB
            if 'skills' in job_data and isinstance(job_data['skills'], list):
                import json
                job_data['skills'] = json.dumps(job_data['skills'])
            
            # Insert query
            columns = ', '.join(job_data.keys())
            placeholders = ', '.join(['%s'] * len(job_data))
            query = f"INSERT INTO jobs ({columns}) VALUES ({placeholders}) ON CONFLICT (source_url) DO NOTHING"
            
            self.cursor.execute(query, list(job_data.values()))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                self.stats['jobs_new'] += 1
                self.logger.debug(f"Inserted job: {job_data['title']}")
                return True
            else:
                self.stats['jobs_skipped'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"Error inserting job: {e}")
            self.conn.rollback()
            self.stats['errors'] += 1
            return False
    
    def update_job(self, source_url: str, job_data: Dict[str, Any]) -> bool:
        """
        Update existing job in database
        
        Args:
            source_url: Job URL to update
            job_data: Updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build SET clause
            set_clause = ', '.join([f"{k} = %s" for k in job_data.keys()])
            values = list(job_data.values())
            values.append(source_url)
            
            query = f"UPDATE jobs SET {set_clause}, last_updated = NOW() WHERE source_url = %s"
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                self.stats['jobs_updated'] += 1
                self.logger.debug(f"Updated job: {source_url}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating job: {e}")
            self.conn.rollback()
            return False
    
    def log_scrape_run(self, start_time: datetime, scrape_mode: str = 'incremental') -> None:
        """
        Log scraping run to scrape_logs table
        
        Args:
            start_time: When scraping started
            scrape_mode: 'incremental' or 'full_refresh'
        """
        try:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            status = 'success'
            if self.stats['errors'] > 0:
                if self.stats['jobs_new'] > 0:
                    status = 'partial'
                else:
                    status = 'failed'
            
            self.cursor.execute("""
                INSERT INTO scrape_logs (
                    site_name, scrape_mode, start_time, end_time, duration_seconds,
                    jobs_found, jobs_new, jobs_updated, jobs_skipped, 
                    status, error_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.site_name, scrape_mode, start_time, end_time, duration,
                self.stats['jobs_found'], self.stats['jobs_new'], 
                self.stats['jobs_updated'], self.stats['jobs_skipped'],
                status, self.stats['errors']
            ))
            self.conn.commit()
            
            self.logger.info(
                f"Scrape completed: {self.stats['jobs_new']} new, "
                f"{self.stats['jobs_updated']} updated, "
                f"{self.stats['jobs_skipped']} skipped, "
                f"{self.stats['errors']} errors"
            )
            
        except Exception as e:
            self.logger.error(f"Error logging scrape run: {e}")
            self.conn.rollback()
    
    def extract_salary(self, salary_text: str) -> Dict[str, Any]:
        """
        Parse salary text into min/max/currency
        
        Args:
            salary_text: Raw salary string (e.g., "PKR 50,000 - 80,000")
            
        Returns:
            Dictionary with salary_min, salary_max, salary_currency
        """
        import re
        
        result = {
            'salary_text': salary_text,
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'PKR'
        }
        
        if not salary_text:
            return result
        
        # Extract currency
        if 'USD' in salary_text.upper() or '$' in salary_text:
            result['salary_currency'] = 'USD'
        
        # Extract numbers (remove commas)
        numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
        numbers = [int(n) for n in numbers if n]
        
        if len(numbers) >= 2:
            result['salary_min'] = min(numbers)
            result['salary_max'] = max(numbers)
        elif len(numbers) == 1:
            result['salary_min'] = numbers[0]
            result['salary_max'] = numbers[0]
        
        return result
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        import re
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    @abstractmethod
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """
        Main scraping method - must be implemented by child classes
        
        Args:
            mode: 'incremental' or 'full_refresh'
            
        Returns:
            Dictionary with scraping statistics
        """
        pass
    
    @abstractmethod
    def parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
        """
        Parse individual job listing - must be implemented by child classes
        
        Args:
            job_element: BeautifulSoup element or dict representing a job
            
        Returns:
            Dictionary with job data or None if parsing failed
        """
        pass
    
    def run(self, mode: str = 'incremental') -> Dict[str, int]:
        """
        Execute scraping process with error handling
        
        Args:
            mode: 'incremental' or 'full_refresh'
            
        Returns:
            Scraping statistics
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting {mode} scrape for {self.site_name}")
            self.connect_db()
            
            # Run site-specific scraping logic
            stats = self.scrape(mode=mode)
            
            # Log the run
            self.log_scrape_run(start_time, mode)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Scraping failed for {self.site_name}: {e}", exc_info=True)
            self.stats['errors'] += 1
            
            # Still try to log the failed run
            try:
                self.log_scrape_run(start_time, mode)
            except:
                pass
            
            return self.stats
            
        finally:
            self.close_db()
