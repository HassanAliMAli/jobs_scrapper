"""
Indeed.pk scraper - Global job platform with Pakistan presence
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .base import BaseScraper


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.pk job listings"""
    
    def __init__(self):
        super().__init__(
            site_name='indeed',
            base_url='https://pk.indeed.com'
        )
        self.search_url = f'{self.base_url}/jobs'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """Scrape Indeed.pk job listings"""
        start = 0
        consecutive_seen = 0
        
        while start < self.max_pages * 10:  # Indeed uses offset (10 jobs per page)
            self.logger.info(f"Scraping from offset {start}...")
            
            params = {
                'q': '',  # All jobs
                'l': 'Pakistan',
                'start': start,
                'fromage': '1' if mode == 'incremental' else None  # Last 1 day for incremental
            }
            
            response = self.make_request(self.search_url, params=params)
            if not response:
                break
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            # Find job cards
            job_cards = soup.find_all('div', class_='job_seen_beacon') or soup.find_all('a', class_='tapItem')
            
            if not job_cards:
                self.logger.info(f"No jobs at offset {start}")
                break
            
            for card in job_cards:
                job_data = self.parse_job_listing(card)
                
                if job_data:
                    self.stats['jobs_found'] += 1
                    
                    if not self.job_exists(job_data['source_url']):
                        self.insert_job(job_data)
                        consecutive_seen = 0
                    else:
                        consecutive_seen += 1
                        if mode == 'incremental' and consecutive_seen >= 15:
                            return self.stats
            
            start += 10
        
        return self.stats
    
    def parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
        """Parse Indeed job card"""
        try:
            job_data = {'site_source': self.site_name}
            
            # Title and URL
            title_elem = job_element.find('h2', class_='jobTitle') or job_element.find('a', id=lambda x: x and 'job_' in x)
            if title_elem:
                title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if title_link:
                    job_data['title'] = self.clean_text(title_link.get_text())
                    job_id = title_link.get('data-jk') or title_link.get('id', '').replace('job_', '')
                    job_data['source_url'] = f"{self.base_url}/viewjob?jk={job_id}"
            
            if 'source_url' not in job_data:
                return None
            
            # Company
            company_elem = job_element.find('span', class_='companyName')
            if company_elem:
                job_data['company'] = self.clean_text(company_elem.get_text())
            else:
                job_data['company'] = 'Unknown'
            
            # Location
            location_elem = job_element.find('div', class_='companyLocation')
            if location_elem:
                location = self.clean_text(location_elem.get_text())
                job_data['location'] = location
                job_data['city'] = location.split(',')[0].strip()
            
            # Salary
            salary_elem = job_element.find('div', class_='salary-snippet')
            if salary_elem:
                job_data.update(self.extract_salary(salary_elem.get_text()))
            
            # Job snippet (short description)
            snippet_elem = job_element.find('div', class_='job-snippet')
            if snippet_elem:
                job_data['description'] = self.clean_text(snippet_elem.get_text())
            
            # Date posted
            date_elem = job_element.find('span', class_='date')
            if date_elem:
                job_data['posted_date'] = self.parse_indeed_date(date_elem.get_text())
            
            # Remote/hybrid detection
            remote_elem = job_element.find('div', class_='remote')
            if remote_elem or 'remote' in job_data.get('title', '').lower():
                job_data['is_remote'] = True
                job_data['is_onsite'] = False
            
            return job_data
            
        except Exception as e:
            self.logger.error(f"Error parsing Indeed job: {e}")
            return None
    
    def parse_indeed_date(self, date_text: str) -> datetime.date:
        """Parse Indeed date formats"""
        import re
        
        date_text = date_text.lower().strip()
        today = datetime.now().date()
        
        if 'just posted' in date_text or 'today' in date_text:
            return today
        
        match = re.search(r'(\d+)', date_text)
        if match:
            num = int(match.group(1))
            if 'day' in date_text:
                return today - timedelta(days=num)
            elif 'hour' in date_text:
                return today
        
        return today
