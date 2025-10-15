"""
Unit tests for REST API
"""

import pytest
import json
from app import app


@pytest.fixture
def client():
    """Test client for Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert 'status' in data


class TestJobsAPI:
    """Test Jobs API endpoints"""
    
    def test_jobs_list(self, client):
        """Test GET /api/v1/jobs"""
        response = client.get('/api/v1/jobs')
        
        # Should return 200 or 500 (if DB not connected)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'jobs' in data
            assert 'total' in data
            assert 'page' in data
    
    def test_jobs_pagination(self, client):
        """Test pagination parameters"""
        response = client.get('/api/v1/jobs?page=2&limit=50')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['page'] == 2
            assert data['limit'] == 50
    
    def test_jobs_search(self, client):
        """Test GET /api/v1/jobs/search"""
        response = client.get('/api/v1/jobs/search?q=python&city=karachi')
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'jobs' in data


class TestStatsAPI:
    """Test Statistics API"""
    
    def test_stats_endpoint(self, client):
        """Test GET /api/v1/stats"""
        response = client.get('/api/v1/stats')
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'total_jobs' in data


class TestWebRoutes:
    """Test web dashboard routes"""
    
    def test_home_page(self, client):
        """Test home page"""
        response = client.get('/')
        assert response.status_code in [200, 500]
    
    def test_jobs_page(self, client):
        """Test jobs page"""
        response = client.get('/jobs')
        assert response.status_code in [200, 500]
    
    def test_scrapers_page(self, client):
        """Test scrapers page"""
        response = client.get('/scrapers')
        assert response.status_code in [200, 500]
    
    def test_analytics_page(self, client):
        """Test analytics page"""
        response = client.get('/analytics')
        assert response.status_code in [200, 500]
