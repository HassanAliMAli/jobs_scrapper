"""
Bayrozgar.com scraper - Urdu content, local Pakistani jobs
"""

from typing import Dict, Optional, Any
from .base import BaseScraper


class BayrozgarScraper(BaseScraper):
    """Scraper for Bayrozgar.com"""
    
    def __init__(self):
        super().__init__(
            site_name='bayrozgar',
            base_url='https://www.bayrozgar.com'
        )
        self.jobs_url = f'{self.base_url}/jobs'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """Scrape Bayrozgar jobs"""
        page = 1
        
        while page <= self.max_pages:
            response = self.make_request(f"{self.jobs_url}/page/{page}")
            if not response:
                break
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            jobs = soup.find_all('div', class_='job-list-item') or soup.find_all('article')
            if not jobs:
                break
            
            for job in jobs:
                job_data = self.parse_job_listing(job)
                if job_data and not self.job_exists(job_data['source_url']):
                    self.insert_job(job_data)
            
            page += 1
        
        return self.stats
    
    def parse_job_listing(self, elem) -> Optional[Dict[str, Any]]:
        """Parse Bayrozgar job"""
        try:
            data = {'site_source': self.site_name}
            
            title_link = elem.find('a', class_='job-title') or elem.find('h2').find('a')
            if title_link:
                data['title'] = self.clean_text(title_link.get_text())
                data['source_url'] = title_link.get('href') if title_link.get('href', '').startswith('http') else f"{self.base_url}{title_link.get('href')}"
            else:
                return None
            
            company = elem.find('div', class_='company')
            data['company'] = self.clean_text(company.get_text()) if company else 'Unknown'
            
            return data
        except:
            return None
