"""
Mustakbil.com scraper - Pakistan's second largest job portal
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .base import BaseScraper


class MustakbilScraper(BaseScraper):
    """Scraper for Mustakbil.com job listings"""
    
    def __init__(self):
        super().__init__(
            site_name='mustakbil',
            base_url='https://www.mustakbil.com'
        )
        self.jobs_url = f'{self.base_url}/jobs/'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """Scrape Mustakbil.com job listings"""
        page = 1
        consecutive_seen = 0
        
        while page <= self.max_pages:
            self.logger.info(f"Scraping page {page}...")
            
            page_url = f"{self.jobs_url}?page={page}"
            response = self.make_request(page_url)
            
            if not response:
                break
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            # Find job cards
            job_elements = soup.find_all('div', class_='job-listing') or soup.find_all('article', class_='job')
            
            if not job_elements:
                self.logger.info(f"No jobs found on page {page}")
                break
            
            for job_elem in job_elements:
                job_data = self.parse_job_listing(job_elem)
                
                if job_data:
                    self.stats['jobs_found'] += 1
                    
                    if not self.job_exists(job_data['source_url']):
                        self.insert_job(job_data)
                        consecutive_seen = 0
                    else:
                        consecutive_seen += 1
                        if mode == 'incremental' and consecutive_seen >= 20:
                            return self.stats
            
            page += 1
        
        return self.stats
    
    def parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
        """Parse individual Mustakbil job listing"""
        try:
            job_data = {'site_source': self.site_name}
            
            # Title and URL
            title_link = job_element.find('a', class_='job-link') or job_element.find('h2').find('a')
            if title_link:
                job_data['title'] = self.clean_text(title_link.get_text())
                job_url = title_link.get('href', '')
                if not job_url.startswith('http'):
                    job_url = f"{self.base_url}{job_url}"
                job_data['source_url'] = job_url
            else:
                return None
            
            # Company
            company_elem = job_element.find('a', class_='company-name') or job_element.find('div', class_='company')
            if company_elem:
                job_data['company'] = self.clean_text(company_elem.get_text())
            else:
                job_data['company'] = 'Unknown'
            
            # Location
            location_elem = job_element.find('span', class_='location') or job_element.find('div', class_='location')
            if location_elem:
                location = self.clean_text(location_elem.get_text())
                job_data['location'] = location
                job_data['city'] = location.split(',')[0].strip() if ',' in location else location
            
            # Salary
            salary_elem = job_element.find('div', class_='salary')
            if salary_elem:
                job_data.update(self.extract_salary(salary_elem.get_text()))
            
            # Experience
            exp_elem = job_element.find('span', class_='experience')
            if exp_elem:
                job_data['experience_years'] = self.clean_text(exp_elem.get_text())
            
            # Job type
            type_elem = job_element.find('span', class_='job-type')
            if type_elem:
                job_data['job_type'] = self.clean_text(type_elem.get_text())
            
            # Posted date
            date_elem = job_element.find('time') or job_element.find('span', class_='posted-date')
            if date_elem:
                job_data['posted_date'] = self.parse_relative_date(date_elem.get_text())
            
            return job_data
            
        except Exception as e:
            self.logger.error(f"Error parsing Mustakbil job: {e}")
            return None
    
    def parse_relative_date(self, date_text: str) -> datetime.date:
        """Parse date like '3 days ago', 'Today'"""
        import re
        
        date_text = date_text.lower().strip()
        today = datetime.now().date()
        
        if 'today' in date_text:
            return today
        elif 'yesterday' in date_text:
            return today - timedelta(days=1)
        
        match = re.search(r'(\d+)', date_text)
        if match:
            num = int(match.group(1))
            if 'day' in date_text:
                return today - timedelta(days=num)
            elif 'week' in date_text:
                return today - timedelta(weeks=num)
            elif 'month' in date_text:
                return today - timedelta(days=num * 30)
        
        return today
