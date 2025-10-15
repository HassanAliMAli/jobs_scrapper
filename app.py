"""
PakJobs Aggregator - Main Flask Application
Web dashboard, REST API, and scheduler
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

import psycopg2
from psycopg2.extras import RealDictCursor
import pytz
from dotenv import load_dotenv

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_restful import Api, Resource
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler

from scrapers import SCRAPERS
from data_pipeline import JobExporter, DatabaseConnector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False

# Enable CORS
CORS(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Initialize REST API
api = Api(app)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Karachi'))


def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def run_scraper(site_name: str, mode: str = 'incremental') -> Dict[str, Any]:
    """
    Run a specific scraper
    
    Args:
        site_name: Name of the site to scrape
        mode: 'incremental' or 'full_refresh'
        
    Returns:
        Scraping statistics
    """
    try:
        scraper_class = SCRAPERS.get(site_name)
        if not scraper_class:
            return {'error': f'Unknown scraper: {site_name}'}
        
        logger.info(f"Running {site_name} scraper in {mode} mode")
        scraper = scraper_class()
        stats = scraper.run(mode=mode)
        
        logger.info(f"{site_name} scraper completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Scraper {site_name} failed: {e}", exc_info=True)
        return {'error': str(e)}


def run_all_scrapers(mode: str = 'incremental'):
    """Run all scrapers sequentially"""
    logger.info(f"Starting all scrapers in {mode} mode")
    results = {}
    
    for site_name in SCRAPERS.keys():
        results[site_name] = run_scraper(site_name, mode)
    
    logger.info(f"All scrapers completed: {results}")
    return results


# =============================================================================
# WEB DASHBOARD ROUTES
# =============================================================================

@app.route('/')
def index():
    """Home page - System overview"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Database connection failed"), 500
    
    try:
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as total FROM jobs WHERE is_active = true")
        total_jobs = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(DISTINCT company) as total FROM jobs WHERE is_active = true")
        total_companies = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(DISTINCT city) as total FROM jobs WHERE is_active = true AND city IS NOT NULL")
        total_cities = cursor.fetchone()['total']
        
        # Recent scrapes
        cursor.execute("""
            SELECT site_name, status, jobs_new, start_time, duration_seconds
            FROM scrape_logs
            ORDER BY start_time DESC
            LIMIT 10
        """)
        recent_scrapes = cursor.fetchall()
        
        # Jobs by site
        cursor.execute("""
            SELECT site_source, COUNT(*) as count
            FROM jobs
            WHERE is_active = true
            GROUP BY site_source
            ORDER BY count DESC
        """)
        jobs_by_site = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('home.html',
                             total_jobs=total_jobs,
                             total_companies=total_companies,
                             total_cities=total_cities,
                             recent_scrapes=recent_scrapes,
                             jobs_by_site=jobs_by_site)
    
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return render_template('error.html', message=str(e)), 500


@app.route('/jobs')
def jobs():
    """Jobs search page"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Database connection failed"), 500
    
    try:
        cursor = conn.cursor()
        
        # Get filter parameters
        query = request.args.get('q', '')
        city = request.args.get('city', '')
        site = request.args.get('site', '')
        min_salary = request.args.get('min_salary', type=int)
        remote = request.args.get('remote', type=bool)
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        # Build query
        where_clauses = ["is_active = true"]
        params = []
        
        if query:
            where_clauses.append("""
                to_tsvector('english', title || ' ' || COALESCE(description, '') || ' ' || company)
                @@ plainto_tsquery('english', %s)
            """)
            params.append(query)
        
        if city:
            where_clauses.append("city ILIKE %s")
            params.append(f"%{city}%")
        
        if site:
            where_clauses.append("site_source = %s")
            params.append(site)
        
        if min_salary:
            where_clauses.append("salary_min >= %s")
            params.append(min_salary)
        
        if remote:
            where_clauses.append("is_remote = true")
        
        where_sql = " AND ".join(where_clauses)
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) as total FROM jobs WHERE {where_sql}", params)
        total_results = cursor.fetchone()['total']
        
        # Get jobs
        cursor.execute(f"""
            SELECT id, title, company, location, city, salary_text, salary_min, salary_max,
                   job_type, is_remote, posted_date, source_url, site_source
            FROM jobs
            WHERE {where_sql}
            ORDER BY posted_date DESC, scraped_at DESC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        job_results = cursor.fetchall()
        
        # Get available cities for filter
        cursor.execute("""
            SELECT DISTINCT city, COUNT(*) as count
            FROM jobs
            WHERE is_active = true AND city IS NOT NULL
            GROUP BY city
            ORDER BY count DESC
            LIMIT 20
        """)
        cities = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        total_pages = (total_results + per_page - 1) // per_page
        
        return render_template('jobs.html',
                             jobs=job_results,
                             total_results=total_results,
                             page=page,
                             total_pages=total_pages,
                             cities=cities,
                             filters={'q': query, 'city': city, 'site': site})
    
    except Exception as e:
        logger.error(f"Error loading jobs page: {e}")
        return render_template('error.html', message=str(e)), 500


@app.route('/scrapers')
def scrapers():
    """Scrapers control page"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Database connection failed"), 500
    
    try:
        cursor = conn.cursor()
        
        # Get latest scrape status for each site
        scraper_status = []
        for site_name in SCRAPERS.keys():
            cursor.execute("""
                SELECT site_name, status, jobs_new, jobs_found, start_time, duration_seconds, error_message
                FROM scrape_logs
                WHERE site_name = %s
                ORDER BY start_time DESC
                LIMIT 1
            """, (site_name,))
            
            result = cursor.fetchone()
            if result:
                scraper_status.append(result)
            else:
                scraper_status.append({
                    'site_name': site_name,
                    'status': 'never_run',
                    'jobs_new': 0,
                    'start_time': None
                })
        
        cursor.close()
        conn.close()
        
        return render_template('scrapers.html', scrapers=scraper_status)
    
    except Exception as e:
        logger.error(f"Error loading scrapers page: {e}")
        return render_template('error.html', message=str(e)), 500


@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Database connection failed"), 500
    
    try:
        cursor = conn.cursor()
        
        # Salary statistics
        cursor.execute("""
            SELECT 
                AVG(salary_min) as avg_min,
                AVG(salary_max) as avg_max,
                MIN(salary_min) as min_salary,
                MAX(salary_max) as max_salary
            FROM jobs
            WHERE is_active = true AND salary_min IS NOT NULL
        """)
        salary_stats = cursor.fetchone()
        
        # Top cities
        cursor.execute("""
            SELECT city, COUNT(*) as count
            FROM jobs
            WHERE is_active = true AND city IS NOT NULL
            GROUP BY city
            ORDER BY count DESC
            LIMIT 10
        """)
        top_cities = cursor.fetchall()
        
        # Top companies
        cursor.execute("""
            SELECT company, COUNT(*) as count
            FROM jobs
            WHERE is_active = true
            GROUP BY company
            ORDER BY count DESC
            LIMIT 10
        """)
        top_companies = cursor.fetchall()
        
        # Jobs over time (last 30 days)
        cursor.execute("""
            SELECT DATE(posted_date) as date, COUNT(*) as count
            FROM jobs
            WHERE posted_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(posted_date)
            ORDER BY date
        """)
        jobs_over_time = cursor.fetchall()
        
        # Remote vs onsite
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_remote THEN 1 ELSE 0 END) as remote_count,
                SUM(CASE WHEN is_hybrid THEN 1 ELSE 0 END) as hybrid_count,
                SUM(CASE WHEN is_onsite THEN 1 ELSE 0 END) as onsite_count
            FROM jobs
            WHERE is_active = true
        """)
        work_mode = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('analytics.html',
                             salary_stats=salary_stats,
                             top_cities=top_cities,
                             top_companies=top_companies,
                             jobs_over_time=jobs_over_time,
                             work_mode=work_mode)
    
    except Exception as e:
        logger.error(f"Error loading analytics page: {e}")
        return render_template('error.html', message=str(e)), 500


@app.route('/run-scraper/<site_name>')
def run_scraper_route(site_name):
    """Manually trigger a scraper"""
    mode = request.args.get('mode', 'incremental')
    
    if site_name == 'all':
        results = run_all_scrapers(mode)
        return jsonify(results)
    else:
        result = run_scraper(site_name, mode)
        return jsonify(result)


@app.route('/export')
def export_jobs():
    """Export jobs to CSV/JSON"""
    format_type = request.args.get('format', 'csv')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get jobs (limit to 10,000)
        cursor.execute("""
            SELECT * FROM jobs
            WHERE is_active = true
            ORDER BY posted_date DESC
            LIMIT 10000
        """)
        
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Export
        exporter = JobExporter()
        
        if format_type == 'json':
            filepath = exporter.export_to_json(jobs)
        elif format_type == 'excel':
            filepath = exporter.export_to_excel(jobs)
        else:  # CSV
            filepath = exporter.export_to_csv(jobs)
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({'status': 'healthy', 'database': 'connected'}), 200
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 503
    except:
        return jsonify({'status': 'unhealthy'}), 503


# =============================================================================
# REST API RESOURCES
# =============================================================================

class JobsListAPI(Resource):
    """GET /api/v1/jobs - List all jobs with pagination"""
    
    def get(self):
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 1000)  # Max 1000 per request
        offset = (page - 1) * limit
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM jobs
                WHERE is_active = true
                ORDER BY posted_date DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            jobs = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as total FROM jobs WHERE is_active = true")
            total = cursor.fetchone()['total']
            
            cursor.close()
            conn.close()
            
            return {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': (total + limit - 1) // limit,
                'jobs': jobs
            }, 200
        
        except Exception as e:
            logger.error(f"API error: {e}")
            return {'error': str(e)}, 500


class JobSearchAPI(Resource):
    """GET /api/v1/jobs/search - Search jobs"""
    
    def get(self):
        query = request.args.get('q', '')
        city = request.args.get('city', '')
        site = request.args.get('site', '')
        limit = request.args.get('limit', 100, type=int)
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
        
        try:
            cursor = conn.cursor()
            
            where_clauses = ["is_active = true"]
            params = []
            
            if query:
                where_clauses.append("""
                    to_tsvector('english', title || ' ' || COALESCE(description, ''))
                    @@ plainto_tsquery('english', %s)
                """)
                params.append(query)
            
            if city:
                where_clauses.append("city ILIKE %s")
                params.append(f"%{city}%")
            
            if site:
                where_clauses.append("site_source = %s")
                params.append(site)
            
            where_sql = " AND ".join(where_clauses)
            
            cursor.execute(f"""
                SELECT * FROM jobs
                WHERE {where_sql}
                ORDER BY posted_date DESC
                LIMIT %s
            """, params + [limit])
            
            jobs = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return {'total': len(jobs), 'jobs': jobs}, 200
        
        except Exception as e:
            logger.error(f"Search API error: {e}")
            return {'error': str(e)}, 500


class StatsAPI(Resource):
    """GET /api/v1/stats - Get statistics"""
    
    def get(self):
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
        
        try:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute("SELECT COUNT(*) as total FROM jobs WHERE is_active = true")
            stats['total_jobs'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(DISTINCT company) as total FROM jobs WHERE is_active = true")
            stats['total_companies'] = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT site_source, COUNT(*) as count
                FROM jobs
                WHERE is_active = true
                GROUP BY site_source
            """)
            stats['by_site'] = {row['site_source']: row['count'] for row in cursor.fetchall()}
            
            cursor.close()
            conn.close()
            
            return stats, 200
        
        except Exception as e:
            logger.error(f"Stats API error: {e}")
            return {'error': str(e)}, 500


# Register API endpoints
api.add_resource(JobsListAPI, '/api/v1/jobs')
api.add_resource(JobSearchAPI, '/api/v1/jobs/search')
api.add_resource(StatsAPI, '/api/v1/stats')


# =============================================================================
# SCHEDULER
# =============================================================================

scheduler = BackgroundScheduler(timezone=TIMEZONE)

# Daily scraping at 3 AM PKT
scheduler.add_job(
    func=lambda: run_all_scrapers('incremental'),
    trigger='cron',
    hour=3,
    minute=0,
    id='daily_scrape'
)

# Weekly full refresh on Sunday at 2 AM
scheduler.add_job(
    func=lambda: run_all_scrapers('full_refresh'),
    trigger='cron',
    day_of_week='sun',
    hour=2,
    minute=0,
    id='weekly_full_refresh'
)

scheduler.start()
logger.info("Scheduler started - Daily scraping at 3 AM PKT")


# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
