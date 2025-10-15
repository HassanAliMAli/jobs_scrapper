"""
Unit tests for data pipeline
"""

import pytest
from data_pipeline.cleaner import DataCleaner
from data_pipeline.exporters import JobExporter


class TestDataCleaner:
    """Test data cleaning utilities"""
    
    def test_clean_text(self):
        """Test text cleaning"""
        assert DataCleaner.clean_text("  Hello   World  ") == "Hello World"
        assert DataCleaner.clean_text("Test\n\tString") == "Test String"
    
    def test_normalize_city(self):
        """Test city normalization"""
        assert DataCleaner.normalize_city("Khi") == "Karachi"
        assert DataCleaner.normalize_city("Isb") == "Islamabad"
        assert DataCleaner.normalize_city("Lhr") == "Lahore"
        assert DataCleaner.normalize_city("Unknown City") == "Unknown City"
    
    def test_extract_skills(self):
        """Test skill extraction"""
        description = "We need a developer with Python, JavaScript, and React experience"
        skills = DataCleaner.extract_skills(description)
        
        assert 'Python' in skills
        assert 'JavaScript' in skills
        assert 'React' in skills
    
    def test_parse_experience_level(self):
        """Test experience level parsing"""
        assert DataCleaner.parse_experience_level("Fresh Graduate") == "Entry Level"
        assert DataCleaner.parse_experience_level("3-5 years") == "Mid Level"
        assert DataCleaner.parse_experience_level("Senior Developer") == "Senior Level"
        assert DataCleaner.parse_experience_level("Director of Engineering") == "Executive"
    
    def test_extract_email(self):
        """Test email extraction"""
        text = "Send resume to jobs@company.com"
        email = DataCleaner.extract_email(text)
        assert email == "jobs@company.com"
    
    def test_extract_url(self):
        """Test URL extraction"""
        text = "Apply at https://www.company.com/careers"
        url = DataCleaner.extract_url(text)
        assert url == "https://www.company.com/careers"
    
    def test_clean_salary(self):
        """Test salary cleaning"""
        result = DataCleaner.clean_salary(50000, 80000, 'PKR')
        assert result['salary_min'] == 50000
        assert result['salary_max'] == 80000
        
        # Swap if min > max
        result = DataCleaner.clean_salary(80000, 50000, 'PKR')
        assert result['salary_min'] == 50000
        assert result['salary_max'] == 80000
    
    def test_deduplicate_jobs(self):
        """Test job deduplication"""
        job1 = {
            'title': 'Software Engineer',
            'company': 'ABC Corp',
            'source_url': 'http://example.com/job1'
        }
        
        job2 = {
            'title': 'Software Engineer',
            'company': 'ABC Corp',
            'source_url': 'http://example.com/job2'
        }
        
        # Same title and company should be duplicate
        assert DataCleaner.deduplicate_jobs(job1, job2) == True
        
        job3 = {
            'title': 'Different Job',
            'company': 'Different Company',
            'source_url': 'http://example.com/job3'
        }
        
        # Different jobs should not be duplicate
        assert DataCleaner.deduplicate_jobs(job1, job3) == False


class TestJobExporter:
    """Test job export functionality"""
    
    @pytest.fixture
    def sample_jobs(self):
        """Sample job data"""
        return [
            {
                'id': '123',
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'city': 'Karachi',
                'salary_min': 80000,
                'salary_max': 120000,
                'skills': ['Python', 'Django', 'PostgreSQL'],
                'site_source': 'rozee'
            },
            {
                'id': '456',
                'title': 'React Developer',
                'company': 'Web Solutions',
                'city': 'Lahore',
                'salary_min': 70000,
                'salary_max': 100000,
                'skills': ['React', 'JavaScript', 'Node.js'],
                'site_source': 'mustakbil'
            }
        ]
    
    def test_export_to_json(self, sample_jobs, tmp_path):
        """Test JSON export"""
        exporter = JobExporter(export_dir=str(tmp_path))
        filepath = exporter.export_to_json(sample_jobs, 'test.json')
        
        assert filepath.endswith('test.json')
        
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert 'jobs' in data
        assert len(data['jobs']) == 2
    
    def test_generate_summary_report(self, sample_jobs):
        """Test summary report generation"""
        exporter = JobExporter()
        summary = exporter.generate_summary_report(sample_jobs)
        
        assert summary['total_jobs'] == 2
        assert 'by_site' in summary
        assert 'salary_stats' in summary
