# Quick Start Guide - PakJobs Aggregator

Get up and running in 5 minutes!

## Prerequisites

- Python 3.12+
- PostgreSQL 16
- Git

## Installation (5 Steps)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
playwright install chromium
```

### 2. Set Up Database

**Create PostgreSQL database:**
```sql
CREATE USER pakjobs_user WITH PASSWORD 'your_password';
CREATE DATABASE pakjobs_dev OWNER pakjobs_user;
```

### 3. Configure Environment

```bash
# Copy template
cp .env.example .env
```

**Edit .env** - Update these required fields:
```bash
DATABASE_URL=postgresql://pakjobs_user:your_password@localhost:5432/pakjobs_dev
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
```

**Generate keys:**
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY  
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Run Application

```bash
python app.py
```

**Open browser**: http://localhost:5000

## First Run

### Test a Scraper

```bash
# Run Rozee scraper (fastest)
python scripts/run_scrapers.py --site rozee --mode incremental
```

This will scrape ~50-100 jobs in 1-2 minutes.

### View Results

1. **Web Dashboard**: http://localhost:5000
2. **Jobs Page**: http://localhost:5000/jobs
3. **API**: http://localhost:5000/api/v1/stats

## Common Commands

```bash
# Run all scrapers
python scripts/run_scrapers.py --site all

# Run specific scraper
python scripts/run_scrapers.py --site mustakbil

# Full refresh (weekly)
python scripts/run_scrapers.py --site all --mode full_refresh

# Export data
curl http://localhost:5000/export?format=csv > jobs.csv

# Run tests
pytest

# Check API
curl http://localhost:5000/api/v1/stats | python -m json.tool
```

## Project Structure

```
pakjobs-aggregator/
├── app.py                 # Flask application (START HERE)
├── schema.sql            # Database schema
├── requirements.txt      # Dependencies
├── scrapers/            # 9 job site scrapers
│   ├── base.py          # Base scraper class
│   ├── rozee.py         # Rozee.pk scraper
│   └── ...              # Other scrapers
├── data_pipeline/       # Data processing
├── templates/           # HTML templates
├── scripts/             # Utility scripts
│   ├── init_db.py       # Initialize database
│   └── run_scrapers.py  # Run scrapers manually
└── tests/               # Test suite
```

## Key Features

✅ **9 Job Site Scrapers**: Rozee, Mustakbil, Indeed, BrightSpyre, Bayt, Jobz, Bayrozgar, JobsAlert, PakPositions  
✅ **Web Dashboard**: Search jobs, view analytics, control scrapers  
✅ **REST API**: JSON endpoints for external apps  
✅ **Data Export**: CSV, JSON, Excel formats  
✅ **Auto-Scheduling**: Daily scraping at 3 AM  
✅ **External DB Push**: PostgreSQL, MySQL, MongoDB  
✅ **100% Free**: Runs on Render.com free tier

## Troubleshooting

**Database connection error?**
```bash
# Check PostgreSQL is running
pg_isready

# Verify .env DATABASE_URL is correct
cat .env | grep DATABASE_URL
```

**Module not found?**
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

**No jobs scraped?**
- Check internet connection
- Verify website is accessible
- Increase delay in .env: `SCRAPE_DELAY_SECONDS=5`

## Next Steps

1. ✅ **Configure Email Notifications**: Add Gmail credentials to `.env`
2. ✅ **Set Up External DB**: Configure database push in dashboard
3. ✅ **Deploy to Production**: Follow INSTALLATION.md for Render deployment
4. ✅ **Customize Scrapers**: Modify scrapers to capture more fields
5. ✅ **Add More Sites**: Create new scrapers for additional job portals

## Documentation

- **Full Installation**: INSTALLATION.md
- **API Reference**: API_DOCUMENTATION.md
- **Contributing**: CONTRIBUTING.md
- **PRD**: prd.md
- **Tasks**: Tasks.md

## Support

- Check logs: `logs/` directory
- Review error messages
- Consult documentation
- Open GitHub issue

---

**You're all set! Happy job scraping! 🚀**
