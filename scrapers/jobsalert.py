"""
JobsAlert.pk scraper - Government sector focus
"""

from typing import Dict, Optional, Any
from .base import BaseScraper


class JobsAlertScraper(BaseScraper):
    """Scraper for JobsAlert.pk"""
    
    def __init__(self):
        super().__init__(
            site_name='jobsalert',
            base_url='https://www.jobsalert.pk'
        )
        self.jobs_url = f'{self.base_url}/jobs'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """Scrape JobsAlert listings"""
        page = 1
        
        while page <= self.max_pages:
            response = self.make_request(f"{self.jobs_url}?page={page}")
            if not response:
                break
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            jobs = soup.find_all('div', class_='job-item') or soup.find_all('article', class_='job')
            if not jobs:
                break
            
            for job in jobs:
                job_data = self.parse_job_listing(job)
                if job_data and not self.job_exists(job_data['source_url']):
                    self.insert_job(job_data)
            
            page += 1
        
        return self.stats
    
    def parse_job_listing(self, elem) -> Optional[Dict[str, Any]]:
        """Parse JobsAlert job"""
        try:
            data = {'site_source': self.site_name}
            
            title = elem.find('a', class_='job-link') or elem.find('h3').find('a')
            if title:
                data['title'] = self.clean_text(title.get_text())
                href = title.get('href', '')
                data['source_url'] = href if href.startswith('http') else f"{self.base_url}{href}"
            else:
                return None
            
            company = elem.find('span', class_='employer')
            data['company'] = self.clean_text(company.get_text()) if company else 'Government/Public Sector'
            
            return data
        except:
            return None
