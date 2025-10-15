"""
Bayt.com scraper - Middle East job portal with Pakistan presence
"""

from typing import Dict, Optional, Any
from .base import BaseScraper


class BaytScraper(BaseScraper):
    """Scraper for Bayt.com Pakistan jobs"""
    
    def __init__(self):
        super().__init__(
            site_name='bayt',
            base_url='https://www.bayt.com'
        )
        self.search_url = f'{self.base_url}/en/pakistan/jobs/'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """Scrape Bayt Pakistan jobs"""
        page = 1
        
        while page <= self.max_pages:
            page_url = f"{self.search_url}?page={page}"
            response = self.make_request(page_url)
            
            if not response:
                break
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            jobs = soup.find_all('li', class_='has-pointer-d') or soup.find_all('div', class_='job-card')
            if not jobs:
                break
            
            for job in jobs:
                job_data = self.parse_job_listing(job)
                if job_data and not self.job_exists(job_data['source_url']):
                    self.insert_job(job_data)
            
            page += 1
        
        return self.stats
    
    def parse_job_listing(self, elem) -> Optional[Dict[str, Any]]:
        """Parse Bayt job listing"""
        try:
            data = {'site_source': self.site_name, 'country': 'Pakistan'}
            
            title_elem = elem.find('h2', class_='jb-title') or elem.find('a', class_='job-title')
            if title_elem:
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                data['title'] = self.clean_text(link.get_text())
                data['source_url'] = f"{self.base_url}{link.get('href')}"
            else:
                return None
            
            company = elem.find('a', class_='comp-name')
            data['company'] = self.clean_text(company.get_text()) if company else 'Unknown'
            
            location = elem.find('span', class_='job-location')
            if location:
                data['location'] = self.clean_text(location.get_text())
            
            return data
        except:
            return None
