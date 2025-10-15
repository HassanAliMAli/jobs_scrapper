"""
Job data validation using Pydantic
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, validator, EmailStr


class JobValidator(BaseModel):
    """Pydantic model for job validation"""
    
    # Required fields
    site_source: str = Field(..., min_length=1, max_length=50)
    source_url: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    
    # Optional fields
    location: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    country: str = Field(default='Pakistan', max_length=50)
    
    # Salary
    salary_text: Optional[str] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: str = Field(default='PKR', max_length=10)
    
    # Content
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    
    # Skills & Qualifications
    skills: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = Field(None, max_length=50)
    experience_years: Optional[str] = Field(None, max_length=50)
    education: Optional[str] = Field(None, max_length=255)
    
    # Job type
    job_type: Optional[str] = Field(None, max_length=50)
    is_remote: bool = Field(default=False)
    is_hybrid: bool = Field(default=False)
    is_onsite: bool = Field(default=True)
    
    # Application
    application_method: Optional[str] = Field(None, max_length=20)
    application_email: Optional[str] = Field(None, max_length=255)
    application_url: Optional[str] = None
    deadline_date: Optional[date] = None
    
    # Dates
    posted_date: Optional[date] = None
    
    # Status
    is_active: bool = Field(default=True)
    
    @validator('site_source')
    def validate_site_source(cls, v):
        """Ensure site source is valid"""
        valid_sites = [
            'rozee', 'mustakbil', 'indeed', 'brightspyre', 'bayt',
            'jobz', 'bayrozgar', 'jobsalert', 'pakpositions'
        ]
        if v.lower() not in valid_sites:
            raise ValueError(f'Invalid site source: {v}')
        return v.lower()
    
    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        """Ensure salary_max >= salary_min"""
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be >= salary_min')
        return v
    
    @validator('application_method')
    def validate_application_method(cls, v):
        """Validate application method"""
        if v and v.lower() not in ['email', 'url', 'unknown']:
            raise ValueError('Invalid application method')
        return v.lower() if v else None
    
    @validator('source_url', 'application_url')
    def validate_url(cls, v):
        """Basic URL validation"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL format')
        return v
    
    @validator('posted_date', 'deadline_date')
    def validate_dates(cls, v):
        """Ensure dates are reasonable"""
        if v:
            today = date.today()
            # Posted date shouldn't be in future
            if v > today:
                return today
            # Don't accept jobs older than 1 year
            if (today - v).days > 365:
                return None
        return v
    
    class Config:
        """Pydantic config"""
        validate_assignment = True
        str_strip_whitespace = True
