"""
Rozee.pk scraper - Pakistan's leading job portal
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .base import BaseScraper
import json
import re


class RozeeScraper(BaseScraper):
    """Scraper for Rozee.pk job listings"""
    
    def __init__(self):
        super().__init__(
            site_name='rozee',
            base_url='https://www.rozee.pk'
        )
        # Rozee loads jobs via JavaScript, so we'll scrape from company listings or use the sitemap
        # For now, let's use a simpler approach: scrape recent jobs from the homepage
        self.search_url = f'{self.base_url}/'
        self.job_detail_urls = []
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        """
        Scrape Rozee.pk job listings with pagination, multiple sources, and smart incremental mode
        
        Args:
            mode: 'incremental' (stops when enough existing jobs found) or 'full_refresh' (scrapes all)
            
        Returns:
            Scraping statistics
        """
        job_urls = []
        
        # Step 1: Define comprehensive job sources with pagination support
        sources = self.get_job_sources(mode)
        
        # Collect job URLs from all sources
        for source_name, source_url, max_pages in sources:
            if self.should_stop():
                break
            
            # Scrape with pagination
            urls_from_source = self.scrape_source_with_pagination(source_name, source_url, max_pages)
            
            # Add to main list (avoiding duplicates)
            for url in urls_from_source:
                if url not in job_urls:
                    job_urls.append(url)
            
            self.logger.info(f"Total unique job URLs collected: {len(job_urls)}")
        
        self.logger.info(f"Total unique job URLs found: {len(job_urls)}")
        total_urls = len(job_urls)
        
        if total_urls == 0:
            self.logger.warning("No job URLs found!")
            return self.stats
        
        # Update progress
        self.update_progress(f"Found {total_urls} job URLs. Starting to scrape...", 20)
        
        # Step 2: Scrape job details with SMART incremental mode
        consecutive_seen = 0
        total_checked = 0
        
        # Smart stopping thresholds for incremental mode
        if mode == 'incremental':
            # Stop if we see 20 consecutive existing jobs OR
            # 80% of checked jobs already exist (after checking at least 50)
            max_consecutive = 20
            min_check_before_percentage = 50
            existing_percentage_threshold = 0.8
        
        for idx, job_url in enumerate(job_urls, 1):
            # Check stop signal
            if self.should_stop():
                self.logger.info(f"Stop signal received at job {idx}")
                break
            
            # Calculate progress (20% to 90% range for scraping)
            progress = 20 + int((idx / total_urls) * 70)
            
            # Update progress
            self.update_progress(
                f"Scraping job {idx}/{total_urls}: {self.stats['jobs_new']} new, {self.stats['jobs_skipped']} skipped",
                progress
            )
            
            self.logger.info(f"Scraping job {idx}/{total_urls}: {job_url}")
            total_checked += 1
            
            # Check if already exists
            if self.job_exists(job_url):
                consecutive_seen += 1
                self.stats['jobs_skipped'] += 1
                
                # Smart incremental mode stopping
                if mode == 'incremental':
                    # Check 1: Too many consecutive existing jobs
                    if consecutive_seen >= max_consecutive:
                        self.logger.info(f"Stopping: {consecutive_seen} consecutive existing jobs found")
                        break
                    
                    # Check 2: High percentage of existing jobs (after minimum checked)
                    if total_checked >= min_check_before_percentage:
                        existing_percentage = self.stats['jobs_skipped'] / total_checked
                        if existing_percentage >= existing_percentage_threshold:
                            self.logger.info(f"Stopping: {existing_percentage*100:.1f}% of jobs already exist (checked {total_checked} jobs)")
                            break
                
                continue
            
            # Reset consecutive counter when we find a new job
            consecutive_seen = 0
            
            # Scrape job details
            job_data = self.scrape_job_detail(job_url)
            
            if job_data:
                self.stats['jobs_found'] += 1
                # Try to insert job
                if not self.insert_job(job_data):
                    # If insert failed, log what we got
                    self.logger.warning(f"Failed to insert job. Data: title={job_data.get('title', 'MISSING')}, company={job_data.get('company', 'MISSING')}")
            else:
                self.logger.error(f"Failed to scrape data from {job_url}")
                self.stats['errors'] += 1
                
            # Be polite - delay between requests
            import time
            time.sleep(self.scrape_delay)
        
        return self.stats
    
    def get_job_sources(self, mode: str) -> list:
        """
        Get comprehensive list of job sources with pagination limits based on mode
        Returns: List of tuples (source_name, base_url, max_pages)
        """
        if mode == 'full_refresh':
            # Full refresh: comprehensive scraping from ALL sources
            sources = []
            
            # TIER 1: Major Cities (11 cities, 3-5 pages each = 44 pages)
            major_cities = [
                ('Karachi', 5),
                ('Lahore', 5),
                ('Islamabad', 5),
                ('Rawalpindi', 3),
                ('Faisalabad', 3),
                ('Multan', 3),
                ('Hyderabad', 3),
                ('Peshawar', 3),
                ('Quetta', 3),
                ('Gujranwala', 3),
                ('Sialkot', 3),
            ]
            for city, pages in major_cities:
                sources.append((f'{city} Jobs', f'https://www.rozee.pk/jobs-in-{city}', pages))
            
            # TIER 2: All Industries (14 industries, 2-3 pages each = 35 pages)
            industries = [
                ('Information Technology', 3),
                ('Banking/Financial Services', 3),
                ('Healthcare/Hospital/Medical', 3),
                ('Education/Teaching', 3),
                ('Sales & Marketing', 3),
                ('Engineering', 3),
                ('Retail', 2),
                ('Real Estate', 2),
                ('Textiles', 2),
                ('Pharmaceutical', 2),
                ('Construction', 2),
                ('Consultants', 2),
                ('Telecom', 2),
                ('Manufacturing', 2),
            ]
            for industry, pages in industries:
                # Format industry name for URL
                industry_url = industry.lower().replace('/', '-').replace(' ', '-')
                sources.append((f'{industry} Jobs', f'https://www.rozee.pk/industry/{industry_url}-jobs', pages))
            
            # TIER 3: Functional Areas/Categories (12 areas, 2 pages each = 24 pages)
            categories = [
                ('Software Development', 2),
                ('Sales & Business Development', 2),
                ('Accounts, Finance & Financial Services', 2),
                ('Human Resources', 2),
                ('Marketing', 2),
                ('Advertising', 2),
                ('Customer Service', 2),
                ('Search Engine Optimization (SEO)', 2),
                ('Data Entry', 2),
                ('Warehousing', 2),
                ('Secretarial, Clerical & Front Office', 2),
                ('Computer Networking', 2),
            ]
            for category, pages in categories:
                # Format category name for URL
                category_url = category.lower().replace('(', '').replace(')', '').replace(',', '').replace('&', '').replace('  ', ' ').replace(' ', '-')
                sources.append((f'{category} Jobs', f'https://www.rozee.pk/category/{category_url}-jobs', pages))
            
            # TIER 4: Special Pages (3 sources, 3 pages each = 9 pages)
            sources.extend([
                ('Homepage', 'https://www.rozee.pk/', 3),
                ('Featured Jobs', 'https://www.rozee.pk/featured-jobs', 3),
                ('Top Jobs', 'https://www.rozee.pk/top-jobs', 3),
            ])
            
            # Total: ~112 pages
            return sources
            
        else:
            # Incremental: focused on recent jobs from key sources (12 pages)
            return [
                # Homepage (most recent)
                ('Homepage', 'https://www.rozee.pk/', 2),
                
                # Top 3 Cities (biggest job markets)
                ('Karachi Jobs', 'https://www.rozee.pk/jobs-in-Karachi', 2),
                ('Lahore Jobs', 'https://www.rozee.pk/jobs-in-Lahore', 2),
                ('Islamabad Jobs', 'https://www.rozee.pk/jobs-in-Islamabad', 2),
                
                # Top 2 Industries (most active)
                ('IT Jobs', 'https://www.rozee.pk/industry/information-technology-jobs', 2),
                ('Banking Jobs', 'https://www.rozee.pk/industry/banking-financial-services-jobs', 2),
            ]
    
    def scrape_source_with_pagination(self, source_name: str, base_url: str, max_pages: int) -> list:
        """
        Scrape job URLs from a source with pagination support
        
        Args:
            source_name: Name of the source for logging
            base_url: Base URL to scrape
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of job URLs found
        """
        job_urls = []
        
        for page_num in range(1, max_pages + 1):
            if self.should_stop():
                break
            
            # Construct page URL
            if page_num == 1:
                page_url = base_url
            else:
                # Rozee.pk pagination pattern
                if '/jsearch/' in base_url:
                    page_url = f"{base_url}?page={page_num}"
                else:
                    # Homepage and other pages might use different pagination
                    page_url = f"{base_url}?page={page_num}"
            
            self.logger.info(f"Fetching {source_name} (page {page_num}/{max_pages})...")
            
            # Fetch page
            response = self.make_request(page_url)
            if not response:
                self.logger.warning(f"Failed to fetch {source_name} page {page_num}")
                # If first page fails, stop. If later page fails, might be end of results
                if page_num == 1:
                    break
                else:
                    continue
            
            soup = self.parse_html(response.text)
            if not soup:
                break
            
            # Find all job links
            job_links = soup.find_all('a', href=re.compile(r'-jobs-\d+$'))
            
            if not job_links:
                self.logger.info(f"No job links found on {source_name} page {page_num}, stopping pagination")
                break
            
            # Extract and normalize URLs
            page_urls_found = 0
            for link in job_links:
                url = link.get('href')
                if url:
                    # Clean and normalize
                    url = url.strip()
                    
                    # Handle different URL formats
                    if url.startswith('http'):
                        full_url = url
                    elif url.startswith('//'):
                        full_url = f"https:{url}"
                    elif url.startswith('/'):
                        full_url = f"{self.base_url}{url}"
                    else:
                        full_url = f"{self.base_url}/{url}"
                    
                    # Clean double slashes
                    full_url = full_url.replace('http://', 'HTTPTEMP').replace('https://', 'HTTPSTEMP')
                    full_url = full_url.replace('//', '/')
                    full_url = full_url.replace('HTTPTEMP', 'http://').replace('HTTPSTEMP', 'https://')
                    
                    # Validate and add
                    if 'rozee.pk' in full_url and '-jobs-' in full_url and full_url not in job_urls:
                        job_urls.append(full_url)
                        page_urls_found += 1
            
            self.logger.info(f"Found {page_urls_found} unique job URLs on {source_name} page {page_num} (total from {source_name}: {len(job_urls)})")
            
            # If we found very few jobs on this page, likely near the end
            if page_urls_found < 5 and page_num > 1:
                self.logger.info(f"Few jobs found on page {page_num}, stopping pagination for {source_name}")
                break
            
            # Small delay between pages
            import time
            time.sleep(0.5)
        
        return job_urls
    
    def scrape_job_detail(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape individual job detail page
        Rozee.pk includes structured JSON-LD data in job pages
        
        Args:
            job_url: URL of the job detail page
            
        Returns:
            Job data dictionary or None
        """
        try:
            response = self.make_request(job_url)
            if not response:
                return None
            
            soup = self.parse_html(response.text)
            if not soup:
                return None
            
            # Look for JSON-LD structured data
            json_ld = soup.find('script', {'type': 'application/ld+json'})
            
            if json_ld:
                try:
                    job_json = json.loads(json_ld.string)
                    
                    # Get title (required field)
                    title = job_json.get('title', '').strip()
                    if not title:
                        self.logger.warning(f"No title found in JSON-LD for {job_url}")
                        return self.parse_job_html(soup, job_url)
                    
                    # Extract data from structured JSON
                    job_data = {
                        'source_site': self.site_name,
                        'apply_url': job_url,
                        'title': title,
                        'company': job_json.get('hiringOrganization', {}).get('name', 'Unknown'),
                        'description': self.clean_html(job_json.get('description', title)),  # Fallback to title
                        'posted_date': self.parse_json_date(job_json.get('datePosted')),
                        'job_type': job_json.get('employmentType', ''),
                    }
                    
                    # Location
                    location = job_json.get('jobLocation', {}).get('address', {})
                    if location:
                        job_data['location'] = location.get('addressLocality', '')
                    
                    # Salary with currency and period
                    salary_info = job_json.get('baseSalary', {}).get('value', {})
                    if salary_info and salary_info.get('value'):
                        job_data['salary'] = salary_info.get('value', '')
                    
                    base_salary = job_json.get('baseSalary', {})
                    if base_salary:
                        job_data['salary_currency'] = base_salary.get('currency', 'PKR')
                        if base_salary.get('value', {}).get('unitText'):
                            job_data['salary_period'] = base_salary['value']['unitText']
                    
                    # Company info
                    hiring_org = job_json.get('hiringOrganization', {})
                    if hiring_org:
                        if hiring_org.get('logo'):
                            job_data['company_logo_url'] = hiring_org['logo']
                        if hiring_org.get('sameAs'):
                            job_data['company_profile_url'] = hiring_org['sameAs']
                    
                    # Application deadline
                    if job_json.get('validThrough'):
                        job_data['application_deadline'] = self.parse_json_date(job_json.get('validThrough'))
                    
                    # External job ID from URL
                    job_data['external_job_id'] = job_url.split('-')[-1] if '-' in job_url else None
                    
                    # Now parse HTML for additional fields not in JSON-LD
                    self.enrich_job_data_from_html(soup, job_data)
                    
                    return job_data
                    
                except Exception as e:
                    self.logger.error(f"Error parsing JSON-LD: {e}")
            
            # Fallback: Try to scrape from HTML
            return self.parse_job_html(soup, job_url)
            
        except Exception as e:
            self.logger.error(f"Error scraping job detail {job_url}: {e}")
            return None
    
    def parse_job_html(self, soup, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to parse job from HTML when JSON-LD not available
        """
        try:
            job_data = {
                'source_site': self.site_name,
                'apply_url': job_url,
            }
            
            # Try to find title - REQUIRED FIELD
            # Look in main content area, NOT sidebars
            title = None
            
            # Try to find main content area first
            main_content = soup.find('div', class_='job-header') or soup.find('main') or soup.find('article')
            
            if main_content:
                title = main_content.find('h1')
            
            # If not found in main content, try page-wide h1 (but filter out sidebar titles)
            if not title:
                for h1 in soup.find_all('h1'):
                    title_text = self.clean_text(h1.get_text())
                    # Skip common sidebar/nav titles
                    if title_text and title_text not in ['Recommended Jobs', 'Similar Jobs', 'Jobs', 'Related Jobs', 'Popular Jobs']:
                        title = h1
                        break
            
            # Extract from page <title> tag as last resort
            if not title:
                page_title = soup.find('title')
                if page_title:
                    title_text = self.clean_text(page_title.get_text())
                    # Remove common suffixes from page title
                    title_text = title_text.replace(' - ROZEE.PK', '').replace(' | ROZEE.PK', '').strip()
                    if title_text and len(title_text) > 5:
                        job_data['title'] = title_text
            
            # If we have a title element, extract text
            if title:
                job_data['title'] = self.clean_text(title.get_text())
            
            # Still no title? Extract from URL
            if not job_data.get('title') or job_data['title'].strip() == '':
                # Extract job title from URL pattern: /company-jobtitle-jobs-123456
                url_parts = job_url.split('/')[-1]
                url_parts = url_parts.replace('-jobs-', '|').split('|')[0]
                job_data['title'] = url_parts.replace('-', ' ').title()
                self.logger.warning(f"Extracted title from URL: {job_data['title']}")
            
            # Validate title is reasonable
            if not job_data.get('title') or len(job_data['title'].strip()) < 3:
                self.logger.error(f"No valid title found for {job_url}")
                return None
            
            # Try to find company name
            company = soup.find('a', href=re.compile(r'/company/'))
            if company:
                job_data['company'] = self.clean_text(company.get_text())
            else:
                job_data['company'] = 'Unknown Company'
            
            # Try to find description
            desc = soup.find('div', class_='job-description') or soup.find('div', {'id': 'job-description'})
            if desc:
                job_data['description'] = self.clean_text(desc.get_text())
            else:
                job_data['description'] = job_data.get('title', 'No description available')
            
            self.logger.info(f"Parsed job from HTML: {job_data['title']} at {job_data['company']}")
            
            # Enrich with additional HTML fields
            self.enrich_job_data_from_html(soup, job_data)
            
            return job_data
            
        except Exception as e:
            self.logger.error(f"Error parsing job HTML: {e}")
            return None
    
    def enrich_job_data_from_html(self, soup, job_data: Dict[str, Any]) -> None:
        """
        Extract additional fields from HTML that are not in JSON-LD
        Modifies job_data in place
        """
        try:
            # Find all the detail rows (they follow pattern: <b>Label:</b> Value)
            rows = soup.find_all('div', class_='row')
            
            for row in rows:
                label_elem = row.find('b')
                if not label_elem:
                    continue
                
                label = self.clean_text(label_elem.get_text()).strip(':').strip()
                value_elem = row.find('div', class_='col-lg-7') or row.find('div', class_='col-md-7')
                
                if not value_elem:
                    continue
                
                value = self.clean_text(value_elem.get_text())
                
                # Map labels to fields
                if label == 'Industry':
                    job_data['industry'] = value
                elif label == 'Functional Area':
                    job_data['functional_area'] = value
                elif label == 'Career Level':
                    job_data['career_level'] = value
                elif label == 'Job Shift':
                    job_data['job_shift'] = value
                elif label == 'Total Positions':
                    # Extract number from "X Post" or "X Posts"
                    positions = value.split()[0]
                    try:
                        job_data['total_positions'] = int(positions)
                    except:
                        job_data['total_positions'] = 1
                elif label == 'Minimum Education':
                    job_data['minimum_education'] = value
                elif label == 'Degree Title':
                    job_data['degree_title'] = value
                elif label == 'Gender':
                    job_data['gender'] = value
                elif label == 'Age':
                    job_data['age_range'] = value
                elif label == 'Apply Before':
                    # Parse date from "Nov 15, 2025" format
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(value, '%b %d, %Y').date()
                        job_data['application_deadline'] = date_obj
                    except:
                        pass
            
            # Try to extract experience from description if not found
            if not job_data.get('minimum_experience'):
                desc = job_data.get('description', '')
                # Look for patterns like "10+ years", "5-7 years", "minimum 3 years"
                import re
                exp_patterns = [
                    r'(\d+\+?\s*(?:to|-)\s*\d+|\d+\+)\s*years?',
                    r'minimum\s+(\d+)\s*years?',
                    r'at least\s+(\d+)\s*years?',
                ]
                for pattern in exp_patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        job_data['minimum_experience'] = match.group(0)
                        break
            
        except Exception as e:
            self.logger.debug(f"Error enriching job data from HTML: {e}")
    
    def clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text)
    
    def parse_json_date(self, date_str: str) -> datetime.date:
        """Parse ISO date string"""
        if not date_str:
            return datetime.now().date()
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except:
            return datetime.now().date()
    
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
                'source_site': self.site_name,
            }
            
            # Job title and URL
            title_elem = job_element.find('h3', class_='job-title') or job_element.find('a', class_='job-title')
            if title_elem:
                job_data['title'] = self.clean_text(title_elem.get_text())
                job_url = title_elem.get('href', '')
                if job_url and not job_url.startswith('http'):
                    job_url = f"{self.base_url}{job_url}"
                job_data['apply_url'] = job_url
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
            
            # Salary
            salary_elem = job_element.find('div', class_='salary') or job_element.find('span', class_='salary')
            if salary_elem:
                job_data['salary'] = self.clean_text(salary_elem.get_text())
            
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
                job_data['experience_level'] = self.clean_text(exp_elem.get_text())
            
            # Skills (if available on listing page)
            skills_elems = job_element.find_all('span', class_='skill-tag')
            if skills_elems:
                job_data['skills'] = [self.clean_text(s.get_text()) for s in skills_elems]
            
            # Description placeholder
            job_data['description'] = job_data['title']
            
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
