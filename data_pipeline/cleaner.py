"""
Data cleaning utilities for job listings
"""

import re
from typing import Dict, Any, List, Optional


class DataCleaner:
    """Clean and normalize job data"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Remove extra whitespace and normalize text"""
        if not text:
            return ''
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def normalize_city(city: str) -> str:
        """Normalize city names"""
        if not city:
            return ''
        
        city = city.strip().title()
        
        # Common variations
        city_mappings = {
            'Isb': 'Islamabad',
            'Isl': 'Islamabad',
            'Rwp': 'Rawalpindi',
            'Lhr': 'Lahore',
            'Khi': 'Karachi',
            'Khi.': 'Karachi',
            'Multan City': 'Multan',
            'Fsd': 'Faisalabad',
        }
        
        return city_mappings.get(city, city)
    
    @staticmethod
    def extract_skills(description: str, requirements: str = '') -> List[str]:
        """
        Extract technical skills from job description
        
        Args:
            description: Job description text
            requirements: Requirements text
            
        Returns:
            List of identified skills
        """
        if not description:
            return []
        
        # Common Pakistani job market skills
        skill_keywords = [
            # Programming Languages
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'PHP', 
            'Ruby', 'Go', 'Golang', 'Rust', 'Swift', 'Kotlin', 'R', 'Scala',
            
            # Web Technologies
            'HTML', 'CSS', 'React', 'Angular', 'Vue', 'Node.js', 'Django', 
            'Flask', 'Laravel', 'WordPress', 'Next.js', 'Express',
            
            # Mobile Development
            'Android', 'iOS', 'React Native', 'Flutter', 'Xamarin',
            
            # Databases
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Oracle', 
            'MS SQL', 'SQLite', 'Elasticsearch',
            
            # DevOps & Cloud
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
            'Git', 'GitHub', 'GitLab', 'Linux', 'Terraform', 'Ansible',
            
            # Data Science & AI
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 
            'Pandas', 'NumPy', 'Scikit-learn', 'NLP', 'Computer Vision',
            'Data Analysis', 'Power BI', 'Tableau', 'Excel',
            
            # Other Technologies
            'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum', 
            'JIRA', 'SAP', 'ERP', 'CRM', 'Salesforce',
            
            # Design
            'UI/UX', 'Figma', 'Adobe XD', 'Photoshop', 'Illustrator',
            
            # Testing
            'Selenium', 'Jest', 'Pytest', 'JUnit', 'QA', 'Testing',
        ]
        
        combined_text = f"{description} {requirements}".lower()
        found_skills = []
        
        for skill in skill_keywords:
            # Check for whole word match (case-insensitive)
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, combined_text):
                found_skills.append(skill)
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    @staticmethod
    def parse_experience_level(experience_text: str) -> str:
        """
        Determine experience level from text
        
        Returns: 'Entry Level', 'Mid Level', 'Senior Level', 'Executive'
        """
        if not experience_text:
            return 'Not Specified'
        
        text = experience_text.lower()
        
        if any(word in text for word in ['entry', 'junior', 'fresh', 'graduate', '0-2', '0-1', 'fresher']):
            return 'Entry Level'
        elif any(word in text for word in ['mid', 'intermediate', '3-5', '2-5']):
            return 'Mid Level'
        elif any(word in text for word in ['senior', 'lead', 'principal', '5+', '7+', '6-10']):
            return 'Senior Level'
        elif any(word in text for word in ['executive', 'director', 'vp', 'c-level', 'cto', 'ceo']):
            return 'Executive'
        else:
            return 'Mid Level'  # Default
    
    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract email address from text"""
        if not text:
            return None
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_url(text: str) -> Optional[str]:
        """Extract URL from text"""
        if not text:
            return None
        
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None
    
    @staticmethod
    def clean_salary(salary_min: int, salary_max: int, currency: str = 'PKR') -> Dict[str, Any]:
        """
        Validate and normalize salary values
        
        Returns:
            Dict with cleaned salary data
        """
        result = {
            'salary_min': None,
            'salary_max': None,
            'salary_currency': currency
        }
        
        # Basic validation
        if salary_min and salary_min > 0:
            result['salary_min'] = salary_min
        
        if salary_max and salary_max > 0:
            result['salary_max'] = salary_max
        
        # Ensure min <= max
        if result['salary_min'] and result['salary_max']:
            if result['salary_min'] > result['salary_max']:
                result['salary_min'], result['salary_max'] = result['salary_max'], result['salary_min']
        
        # Sanity checks (PKR values)
        if currency == 'PKR':
            # Minimum wage in Pakistan ~25,000 PKR
            if result['salary_min'] and result['salary_min'] < 10000:
                result['salary_min'] = None
            
            # Cap at reasonable max (e.g., 10M PKR/month)
            if result['salary_max'] and result['salary_max'] > 10000000:
                result['salary_max'] = None
        
        return result
    
    @staticmethod
    def deduplicate_jobs(job1: Dict, job2: Dict) -> bool:
        """
        Check if two jobs are duplicates
        
        Args:
            job1, job2: Job dictionaries
            
        Returns:
            True if duplicate, False otherwise
        """
        # Same source URL = definite duplicate
        if job1.get('source_url') == job2.get('source_url'):
            return True
        
        # Check title + company similarity
        title1 = job1.get('title', '').lower().strip()
        title2 = job2.get('title', '').lower().strip()
        company1 = job1.get('company', '').lower().strip()
        company2 = job2.get('company', '').lower().strip()
        
        # Exact match on title and company
        if title1 == title2 and company1 == company2:
            return True
        
        # Fuzzy matching using Levenshtein distance
        try:
            from difflib import SequenceMatcher
            
            title_similarity = SequenceMatcher(None, title1, title2).ratio()
            company_similarity = SequenceMatcher(None, company1, company2).ratio()
            
            # If both are very similar (>90%), consider duplicate
            if title_similarity > 0.9 and company_similarity > 0.9:
                return True
        except:
            pass
        
        return False
