# 🇵🇰 PakJobs Aggregator

**Comprehensive Job Aggregation Platform for Pakistan**

## Overview

PakJobs Aggregator is a zero-cost job scraping and analytics platform that consolidates listings from 9 major Pakistani job portals into a single, searchable database with advanced insights.

## Features

- ✅ **Multi-Site Scraping**: Aggregates from Rozee, Mustakbil, Indeed, BrightSpyre, Bayt, Jobz.pk, Bayrozgar, JobsAlert, PakPositions
- ✅ **Smart Analytics**: Salary trends, skill demand mapping, location heatmaps
- ✅ **REST API**: JSON endpoints for external applications
- ✅ **Data Export**: CSV, JSON, Excel formats
- ✅ **External DB Integration**: Push to PostgreSQL, MySQL, MongoDB
- ✅ **Email Notifications**: Automated scraping reports
- ✅ **100% Free**: Runs on Render.com free tier

## Tech Stack

- **Backend**: Python 3.12+, Flask 3.0
- **Scraping**: Scrapy 2.11, Playwright 1.40
- **Database**: PostgreSQL 16 (1GB)
- **Scheduling**: APScheduler
- **Deployment**: Render.com (free tier)

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/pakjobs-aggregator.git
cd pakjobs-aggregator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/init_db.py

# Run application
python app.py
```

## Project Structure

```
pakjobs-aggregator/
├── app.py                    # Flask application
├── requirements.txt          # Dependencies
├── schema.sql               # Database schema
├── scrapers/                # Scraping modules
│   ├── base.py              # BaseScraper class
│   ├── rozee.py             # Rozee.pk scraper
│   ├── mustakbil.py         # Mustakbil scraper
│   └── ...                  # Other scrapers
├── data_pipeline/           # Data processing
│   ├── cleaner.py           # Data cleaning
│   ├── validator.py         # Validation
│   └── exporters.py         # CSV/JSON export
├── templates/               # HTML templates
├── static/                  # CSS, JS assets
├── tests/                   # Test suite
└── scripts/                 # Utility scripts
```

## Usage

### Web Dashboard

Access the dashboard at `http://localhost:5000`

- **Home**: System status and quick stats
- **Jobs**: Search and filter listings
- **Scrapers**: Control scraper execution
- **Analytics**: Salary trends and insights
- **Settings**: External DB configuration

### API Endpoints

```bash
# Get all jobs (paginated)
GET /api/v1/jobs?page=1&limit=100

# Search jobs
GET /api/v1/jobs/search?q=python&city=karachi

# Get single job
GET /api/v1/jobs/{id}

# Get statistics
GET /api/v1/stats

# Get scraper status
GET /api/v1/sites
```

### Manual Scraping

```bash
# Run all scrapers
python scripts/run_scrapers.py --mode incremental

# Run specific scraper
python scripts/run_scrapers.py --site rozee

# Full refresh (weekly)
python scripts/run_scrapers.py --mode full_refresh
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options:

- **Database**: PostgreSQL connection string
- **Email**: Gmail SMTP for notifications
- **Scraping**: Delays, limits, user agents
- **External DB**: Optional database push configuration

### Scheduling

Scrapers run automatically at 3 AM PKT daily via APScheduler. Configure in `app.py`:

```python
scheduler.add_job(
    func=run_all_scrapers,
    trigger="cron",
    hour=3,
    minute=0,
    timezone=pytz.timezone('Asia/Karachi')
)
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Test specific scraper
pytest tests/test_scrapers.py::test_rozee_scraper
```

## Deployment

### Render.com (Free Tier)

1. Push code to GitHub
2. Connect Render.com to repository
3. Configure environment variables
4. Deploy automatically on push

See `render.yaml` for deployment configuration.

## Legal & Ethics

- Respects `robots.txt` on all sites
- Implements polite scraping (3s delays)
- Scrapes only public job listings
- Provides attribution links
- Off-peak scraping (3 AM)

## Contributing

This is an internal project. For issues or feature requests, open a GitHub issue.

## License

Internal Use - Not for public distribution

## Contact

For questions: admin@pakjobs.example.com

---

**Built with ❤️ for Pakistani job seekers**
