"""
BrightSpyre.com scraper - Tech-focused job listings
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from .base import BaseScraper


class BrightSpyreScraper(BaseScraper):
    """Scraper for BrightSpyre.com job listings"""
    
    def __init__(self):
        super().__init__(
            site_name='brightspyre',
            base_url='https://www.brightspyre.com'
        )
        self.jobs_url = f'{self.base_url}/jobs'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """Scrape BrightSpyre job listings"""
        page = 1
        
        while page <= self.max_pages:
            page_url = f"{self.jobs_url}?page={page}"
            response = self.make_request(page_url)
            
            if not response:
                break
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            jobs = soup.find_all('div', class_='job-item') or soup.find_all('article')
            if not jobs:
                break
            
            for job in jobs:
                job_data = self.parse_job_listing(job)
                if job_data and not self.job_exists(job_data['source_url']):
                    self.insert_job(job_data)
            
            page += 1
        
        return self.stats
    
    def parse_job_listing(self, elem) -> Optional[Dict[str, Any]]:
        """Parse BrightSpyre job"""
        try:
            data = {'site_source': self.site_name}
            
            title_link = elem.find('a', class_='job-title') or elem.find('h3').find('a')
            if title_link:
                data['title'] = self.clean_text(title_link.get_text())
                data['source_url'] = title_link.get('href') if title_link.get('href', '').startswith('http') else f"{self.base_url}{title_link.get('href')}"
            else:
                return None
            
            company = elem.find('div', class_='company-name')
            data['company'] = self.clean_text(company.get_text()) if company else 'Unknown'
            
            location = elem.find('span', class_='location')
            if location:
                data['location'] = self.clean_text(location.get_text())
                data['city'] = data['location'].split(',')[0]
            
            return data
        except:
            return None
