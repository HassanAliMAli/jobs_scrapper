"""
PakPositions.com scraper - SME job postings
"""

from typing import Dict, Optional, Any
from .base import BaseScraper


class PakPositionsScraper(BaseScraper):
    """Scraper for PakPositions.com"""
    
    def __init__(self):
        super().__init__(
            site_name='pakpositions',
            base_url='https://www.pakpositions.com'
        )
        self.jobs_url = f'{self.base_url}/jobs'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """Scrape PakPositions listings"""
        page = 1
        
        while page <= self.max_pages:
            response = self.make_request(f"{self.jobs_url}?page={page}")
            if not response:
                break
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            jobs = soup.find_all('div', class_='job-card') or soup.find_all('article')
            if not jobs:
                break
            
            for job in jobs:
                job_data = self.parse_job_listing(job)
                if job_data and not self.job_exists(job_data['source_url']):
                    self.insert_job(job_data)
            
            page += 1
        
        return self.stats
    
    def parse_job_listing(self, elem) -> Optional[Dict[str, Any]]:
        """Parse PakPositions job"""
        try:
            data = {'site_source': self.site_name}
            
            title_link = elem.find('a', class_='position-link') or elem.find('h2').find('a')
            if title_link:
                data['title'] = self.clean_text(title_link.get_text())
                href = title_link.get('href', '')
                data['source_url'] = href if href.startswith('http') else f"{self.base_url}{href}"
            else:
                return None
            
            company = elem.find('div', class_='company-name')
            data['company'] = self.clean_text(company.get_text()) if company else 'Unknown'
            
            return data
        except:
            return None
