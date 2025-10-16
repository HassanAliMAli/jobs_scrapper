# 🇵🇰 Rozee.pk Job Scraper

**Comprehensive Job Scraping Platform for Rozee.pk**

## Overview

A professional-grade job scraper that aggregates listings from Rozee.pk (Pakistan's largest job portal) with complete coverage of all cities, industries, and functional areas.

## Features

- ✅ **Complete Coverage**: 60-80% of Rozee.pk job market (10,000-18,000 jobs)
- ✅ **40 Sources**: All major cities, industries, and categories
- ✅ **28 Data Fields**: Complete job information including deadlines, salaries, requirements
- ✅ **Smart Scraping**: Intelligent incremental mode with pagination
- ✅ **REST API**: JSON endpoints for job search
- ✅ **Real-time Progress**: Live scraping status and statistics
- ✅ **Web Dashboard**: Modern UI for job search and filtering

## Tech Stack

- **Backend**: Python 3.12+, Flask 3.0
- **Scraping**: BeautifulSoup4, Requests
- **Database**: PostgreSQL 16
- **Scheduling**: APScheduler
- **Frontend**: TailwindCSS

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/rozee-scraper.git
cd rozee-scraper

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env
# Edit .env with your PostgreSQL connection

# Run application
python app.py

# Access dashboard
# http://localhost:8080
```

## Project Structure

```
rozee-scraper/
├── app.py                    # Flask application
├── requirements.txt          # Dependencies
├── schema.sql               # Database schema
├── scrapers/
│   ├── base.py              # BaseScraper class
│   └── rozee.py             # Rozee.pk scraper (40 sources)
├── migrations/
│   └── add_complete_job_fields.sql
├── templates/               # HTML templates
└── static/                  # CSS, JS assets
```

## Usage

### Web Dashboard

Access at `http://localhost:8080`

- **Jobs**: Search and filter 10,000+ jobs
- **Scrapers**: Run incremental or full refresh scraping
- **Analytics**: View scraping statistics

### Scraping Modes

**Incremental (Daily):**
- 6 sources, 12 pages
- ~2,400 job URLs
- 800-1,500 new jobs
- 30-50 minutes

**Full Refresh (Weekly):**
- 40 sources, 112 pages  
- ~22,400 job URLs
- 10,000-18,000 jobs
- 5-8 hours
- **60-80% market coverage**

### API Endpoints

```bash
# Get all jobs
GET /api/v1/jobs?page=1&limit=100

# Search jobs
GET /api/v1/jobs/search?q=python&location=karachi

# Get single job
GET /api/v1/jobs/{id}

# Get statistics
GET /api/v1/stats
```

## Configuration

### Environment Variables (.env)

```
DATABASE_URL=postgresql://user:pass@localhost:5432/jobs_db
PORT=8080
TIMEZONE=Asia/Karachi
```

### Scheduling

Scraper runs automatically at 3 AM PKT daily (incremental mode)

## Data Fields Scraped

All **28 fields** per job:
- Basic: Title, Company, Description, URL, Posted Date
- Classification: Industry, Functional Area, Career Level, Job Type, Shift
- Location: City, Is Remote
- Requirements: Min Education, Degree, Experience, Age, Gender, Skills
- Compensation: Salary, Currency, Period
- Deadlines: Application Deadline, Total Positions
- Company: Logo URL, Profile URL
- Meta: External Job ID, Active Status

## Coverage Details

### Cities (11)
Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Multan, Hyderabad, Peshawar, Quetta, Gujranwala, Sialkot

### Industries (14)
IT, Banking, Healthcare, Education, Sales & Marketing, Engineering, Retail, Real Estate, Textiles, Pharmaceutical, Construction, Consultants, Telecom, Manufacturing

### Functional Areas (12)
Software Development, Sales & Business, Accounts & Finance, HR, Marketing, Advertising, Customer Service, SEO, Data Entry, Warehousing, Secretarial, Computer Networking

## License

MIT License

---

**Built with ❤️ for Pakistani job seekers**
