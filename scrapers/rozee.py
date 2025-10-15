"""
Rozee.pk scraper - Pakistan's leading job portal
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .base import BaseScraper


class RozeeScraper(BaseScraper):
    """Scraper for Rozee.pk job listings"""
    
    def __init__(self):
        super().__init__(
            site_name='rozee',
            base_url='https://www.rozee.pk'
        )
        self.search_url = f'{self.base_url}/job/jsearch/q/all/fpn/'
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """
        Scrape Rozee.pk job listings
        
        Args:
            mode: 'incremental' or 'full_refresh'
            
        Returns:
            Scraping statistics
        """
        page = 1
        consecutive_seen = 0
        max_consecutive_seen = 20  # Stop if 20 jobs in a row already exist
        
        while page <= self.max_pages:
            self.logger.info(f"Scraping page {page}...")
            
            # Fetch page
            page_url = f"{self.search_url}{page}"
            response = self.make_request(page_url)
            
            if not response:
                self.logger.warning(f"Failed to fetch page {page}, stopping")
                break
            
            # Parse HTML
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            # Find job listings
            job_elements = soup.find_all('div', class_='job')
            
            if not job_elements:
                self.logger.info(f"No jobs found on page {page}, stopping")
                break
            
            self.logger.info(f"Found {len(job_elements)} jobs on page {page}")
            
            # Process each job
            for job_elem in job_elements:
                job_data = self.parse_job_listing(job_elem)
                
                if job_data:
                    self.stats['jobs_found'] += 1
                    
                    # Check if exists
                    if self.job_exists(job_data['source_url']):
                        consecutive_seen += 1
                        
                        # In incremental mode, stop early if seeing too many existing jobs
                        if mode == 'incremental' and consecutive_seen >= max_consecutive_seen:
                            self.logger.info(f"Seen {consecutive_seen} existing jobs, stopping incremental scrape")
                            return self.stats
                    else:
                        consecutive_seen = 0
                        self.insert_job(job_data)
            
            page += 1
        
        return self.stats
    
    def parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
        """
        Parse individual Rozee job listing
        
        Args:
            job_element: BeautifulSoup job element
            
        Returns:
            Job data dictionary or None
        """
        try:
            job_data = {
                'site_source': self.site_name,
            }
            
            # Job title and URL
            title_elem = job_element.find('h3', class_='job-title') or job_element.find('a', class_='job-title')
            if title_elem:
                job_data['title'] = self.clean_text(title_elem.get_text())
                job_url = title_elem.get('href', '')
                if job_url and not job_url.startswith('http'):
                    job_url = f"{self.base_url}{job_url}"
                job_data['source_url'] = job_url
            else:
                return None
            
            # Company name
            company_elem = job_element.find('div', class_='company') or job_element.find('p', class_='company-name')
            if company_elem:
                job_data['company'] = self.clean_text(company_elem.get_text())
            else:
                job_data['company'] = 'Unknown Company'
            
            # Location
            location_elem = job_element.find('div', class_='location') or job_element.find('span', class_='location')
            if location_elem:
                location_text = self.clean_text(location_elem.get_text())
                job_data['location'] = location_text
                
                # Extract city
                if ',' in location_text:
                    job_data['city'] = location_text.split(',')[0].strip()
                else:
                    job_data['city'] = location_text
            
            # Salary
            salary_elem = job_element.find('div', class_='salary') or job_element.find('span', class_='salary')
            if salary_elem:
                salary_data = self.extract_salary(salary_elem.get_text())
                job_data.update(salary_data)
            
            # Job type
            job_type_elem = job_element.find('span', class_='job-type')
            if job_type_elem:
                job_data['job_type'] = self.clean_text(job_type_elem.get_text())
            
            # Posted date
            date_elem = job_element.find('div', class_='date') or job_element.find('span', class_='date-posted')
            if date_elem:
                date_text = self.clean_text(date_elem.get_text())
                job_data['posted_date'] = self.parse_date(date_text)
            
            # Experience level
            exp_elem = job_element.find('span', class_='experience')
            if exp_elem:
                job_data['experience_years'] = self.clean_text(exp_elem.get_text())
            
            # Skills (if available on listing page)
            skills_elems = job_element.find_all('span', class_='skill-tag')
            if skills_elems:
                job_data['skills'] = [self.clean_text(s.get_text()) for s in skills_elems]
            
            # Work mode detection
            title_lower = job_data['title'].lower()
            if 'remote' in title_lower:
                job_data['is_remote'] = True
                job_data['is_onsite'] = False
            if 'hybrid' in title_lower:
                job_data['is_hybrid'] = True
            
            return job_data
            
        except Exception as e:
            self.logger.error(f"Error parsing job listing: {e}")
            return None
    
    def parse_date(self, date_text: str) -> datetime.date:
        """
        Parse relative date text (e.g., '2 days ago', 'Today', '1 week ago')
        
        Args:
            date_text: Date string
            
        Returns:
            Date object
        """
        import re
        
        date_text = date_text.lower().strip()
        today = datetime.now().date()
        
        if 'today' in date_text or 'just now' in date_text:
            return today
        elif 'yesterday' in date_text:
            return today - timedelta(days=1)
        else:
            # Extract number
            match = re.search(r'(\d+)', date_text)
            if match:
                num = int(match.group(1))
                
                if 'day' in date_text:
                    return today - timedelta(days=num)
                elif 'week' in date_text:
                    return today - timedelta(weeks=num)
                elif 'month' in date_text:
                    return today - timedelta(days=num * 30)
                elif 'hour' in date_text:
                    return today
        
        # Default to today if can't parse
        return today
