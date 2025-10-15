# Installation Guide - PakJobs Aggregator

Complete step-by-step installation guide for local development and production deployment.

## Prerequisites

- **Python**: 3.12 or higher
- **PostgreSQL**: 16 or higher
- **Git**: Latest version
- **OS**: Windows, macOS, or Linux

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/pakjobs-aggregator.git
cd pakjobs-aggregator
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 4. Set Up PostgreSQL Database

**Windows (Download Installer):**
1. Download PostgreSQL 16 from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set for the postgres user

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql-16 postgresql-contrib-16
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 5. Create Database

**Windows (SQL Shell - psql):**
```sql
CREATE USER pakjobs_user WITH PASSWORD 'your_password';
CREATE DATABASE pakjobs_dev OWNER pakjobs_user;
GRANT ALL PRIVILEGES ON DATABASE pakjobs_dev TO pakjobs_user;
```

**macOS/Linux:**
```bash
sudo -u postgres createuser pakjobs_user
sudo -u postgres createdb -O pakjobs_user pakjobs_dev
sudo -u postgres psql -c "ALTER USER pakjobs_user WITH PASSWORD 'your_password';"
```

### 6. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env
```

Edit `.env` file with your settings:

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql://pakjobs_user:your_password@localhost:5432/pakjobs_dev

# Email Notifications (OPTIONAL)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_RECIPIENTS=admin@example.com

# Security Keys (Generate new ones!)
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Application
DEBUG=true
LOG_LEVEL=INFO
TIMEZONE=Asia/Karachi
```

**Generate Secret Keys:**
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Gmail App Password:**
1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate App Password at https://myaccount.google.com/apppasswords
4. Use this password in SMTP_PASSWORD (not your regular password)

### 7. Initialize Database Schema

```bash
python scripts/init_db.py
```

You should see:
```
✅ Database schema created successfully
✅ Tables created: ['analytics_cache', 'jobs', 'scrape_logs', 'user_config']
✅ Default config entries: 10
```

### 8. Run Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

### 9. Test Scrapers (Optional)

```bash
# List available scrapers
python scripts/run_scrapers.py --list

# Run single scraper
python scripts/run_scrapers.py --site rozee --mode incremental

# Run all scrapers
python scripts/run_scrapers.py --site all --mode incremental
```

## Production Deployment (Render.com)

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pakjobs-aggregator.git
git push -u origin main
```

### 2. Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Connect your repository

### 3. Create PostgreSQL Database

1. Click "New +" → "PostgreSQL"
2. Name: `pakjobs-db`
3. Database: `pakjobs`
4. User: `pakjobs_user`
5. Region: Choose closest to Pakistan (e.g., Singapore)
6. Plan: **Free** (1GB storage)
7. Click "Create Database"
8. Wait for provisioning (~2 minutes)
9. Copy the **Internal Database URL** (starts with `postgresql://`)

### 4. Create Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `pakjobs-api`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan**: **Free**

### 5. Add Environment Variables

In the web service settings, add these environment variables:

```
DATABASE_URL = [Paste Internal Database URL from step 3]
FLASK_ENV = production
DEBUG = false
SECRET_KEY = [Generate new secret key]
ENCRYPTION_KEY = [Generate new encryption key]
SMTP_USERNAME = your-email@gmail.com
SMTP_PASSWORD = your-gmail-app-password
SMTP_RECIPIENTS = admin@example.com
TIMEZONE = Asia/Karachi
USER_AGENT = Mozilla/5.0 (compatible; PakJobsBot/1.0)
SCRAPE_DELAY_SECONDS = 3
MAX_SCRAPE_PAGES = 50
```

### 6. Initialize Production Database

Option A - Use Render Shell:
```bash
# In Render dashboard, open Shell for your web service
python scripts/init_db.py
```

Option B - Local psql connection:
```bash
# Copy External Database URL from Render
psql [EXTERNAL_DATABASE_URL]
# Then paste contents of schema.sql
```

### 7. Deploy

1. Click "Create Web Service"
2. Wait for deployment (~5-10 minutes)
3. Your app will be available at `https://pakjobs-api.onrender.com`

### 8. Set Up Automated Scraping

The scheduler is built-in and will automatically run:
- **Daily scraping**: 3 AM PKT (incremental mode)
- **Weekly refresh**: Sunday 2 AM PKT (full refresh)

No additional cron setup needed!

## Verification Checklist

After installation, verify:

- [ ] Database connection works (`/health` endpoint returns 200)
- [ ] Home page loads with statistics
- [ ] Job search works
- [ ] Scrapers page accessible
- [ ] Analytics page shows data (after first scrape)
- [ ] API endpoints respond (`/api/v1/stats`)
- [ ] CSV export works
- [ ] Email notifications sent (if configured)

## Troubleshooting

### Database Connection Failed

**Error**: `could not connect to server`

**Solution**:
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in `.env`
- Check firewall settings
- On Windows, ensure PostgreSQL service is started

### Module Not Found

**Error**: `ModuleNotFoundError: No module named 'scrapy'`

**Solution**:
```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

pip install -r requirements.txt
```

### Playwright Browser Not Found

**Error**: `Executable doesn't exist at ...`

**Solution**:
```bash
playwright install chromium
```

### Render Deployment Failed

**Error**: Build or deploy failed

**Solutions**:
- Check build logs in Render dashboard
- Ensure `runtime.txt` has Python 3.12.0
- Verify `requirements.txt` has all dependencies
- Check DATABASE_URL is set correctly

### Scrapers Return No Jobs

**Possible Causes**:
- Website structure changed (requires scraper update)
- Rate limiting (wait and try again)
- Network issues
- Site blocking bot traffic

**Solution**: Check scraper logs, increase delays, update selectors

## Performance Optimization

### Database Indexing

Indexes are created automatically by `schema.sql`. To verify:

```sql
-- Check indexes
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';
```

### Query Optimization

For large databases (50K+ jobs), enable:

```sql
-- Analyze tables for query planning
ANALYZE jobs;
ANALYZE scrape_logs;
```

### Render Free Tier Limits

- **Web Service**: Spins down after 15 minutes of inactivity
- **Database**: 1GB storage, 97 max connections
- **Bandwidth**: 100GB/month
- **Build Minutes**: 500 hours/month

To stay within limits:
- Keep database under 800MB
- Archive old jobs (90+ days)
- Limit scraping frequency
- Use incremental mode

## Backup & Restore

### Manual Backup

```bash
# Local
pg_dump $DATABASE_URL > backup.sql

# Production (using Render External URL)
pg_dump [EXTERNAL_DATABASE_URL] > production_backup.sql
```

### Automated Backups

```bash
# Make script executable (Linux/Mac)
chmod +x scripts/backup_db.sh

# Run backup
./scripts/backup_db.sh
```

### Restore from Backup

```bash
psql $DATABASE_URL < backup.sql
```

## Upgrading

### Update Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### Update Database Schema

If schema changes, create migration:

```sql
-- Example: Add new column
ALTER TABLE jobs ADD COLUMN new_field VARCHAR(255);
```

### Update Scrapers

When website HTML changes:
1. Identify broken scraper
2. Update CSS selectors in `scrapers/[site].py`
3. Test locally
4. Deploy to production

## Support

For issues:
1. Check logs: `logs/` directory or Render dashboard
2. Review error messages
3. Consult documentation
4. Check GitHub issues

## Next Steps

After successful installation:
1. ✅ Run first scrape: `python scripts/run_scrapers.py --site rozee`
2. ✅ Explore web dashboard: `http://localhost:5000`
3. ✅ Test API: `curl http://localhost:5000/api/v1/stats`
4. ✅ Configure email notifications
5. ✅ Set up external database integration (optional)
6. ✅ Deploy to production

---

**Congratulations! Your PakJobs Aggregator is ready! 🎉**
