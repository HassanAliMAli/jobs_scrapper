# Deployment Checklist - PakJobs Aggregator

Complete checklist for deploying to production.

## ✅ Pre-Deployment Checklist

### 1. Code Review
- [ ] All code follows PEP 8 style guidelines
- [ ] No hardcoded credentials or secrets
- [ ] All TODO comments resolved
- [ ] Error handling implemented for all scrapers
- [ ] Logging configured appropriately

### 2. Testing
- [ ] Run all unit tests: `pytest`
- [ ] Test scrapers individually
- [ ] Verify database schema
- [ ] Test API endpoints
- [ ] Check CSV/JSON exports
- [ ] Validate email notifications

### 3. Security
- [ ] `.env` file not committed to Git
- [ ] New SECRET_KEY generated for production
- [ ] New ENCRYPTION_KEY generated for production
- [ ] Gmail App Password configured (not regular password)
- [ ] Database credentials secure
- [ ] Rate limiting enabled on API

### 4. Documentation
- [ ] README.md updated
- [ ] API documentation complete
- [ ] Environment variables documented
- [ ] Deployment steps clear

### 5. Dependencies
- [ ] requirements.txt up to date
- [ ] All packages compatible
- [ ] Playwright browsers will install on deployment

## 🚀 Local Deployment

### Step 1: Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Database Setup
```bash
# Create PostgreSQL database
createdb pakjobs_dev

# Initialize schema
python scripts/init_db.py
```

### Step 3: Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or use any text editor
```

### Step 4: Verification
```bash
# Run verification script
python verify_setup.py

# Should show all checks passed
```

### Step 5: Run Application
```bash
# Start Flask app
python app.py

# Open browser: http://localhost:5000
```

### Step 6: Test Scrapers
```bash
# Run single scraper
python scripts/run_scrapers.py --site rozee --mode incremental

# Verify jobs in database
psql pakjobs_dev -c "SELECT COUNT(*) FROM jobs;"
```

## ☁️ Render.com Deployment

### Step 1: GitHub Setup
```bash
# Initialize Git (if not done)
git init
git add .
git commit -m "Initial commit: PakJobs Aggregator"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/pakjobs-aggregator.git
git push -u origin main
```

### Step 2: Render Database
1. Login to https://render.com
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: pakjobs-db
   - **Database**: pakjobs
   - **User**: pakjobs_user
   - **Region**: Singapore (closest to Pakistan)
   - **Plan**: Free
4. Click "Create Database"
5. Wait for provisioning (~2 minutes)
6. Copy **Internal Database URL**

### Step 3: Render Web Service
1. Click "New +" → "Web Service"
2. Connect GitHub repository
3. Configure:
   - **Name**: pakjobs-api
   - **Region**: Singapore
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: 
     ```
     pip install -r requirements.txt && playwright install chromium
     ```
   - **Start Command**:
     ```
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
     ```
   - **Plan**: Free

### Step 4: Environment Variables
Add these in Render dashboard:

```bash
DATABASE_URL=[Paste Internal Database URL from Step 2]
FLASK_ENV=production
DEBUG=false
SECRET_KEY=[Generate new: python -c "import secrets; print(secrets.token_hex(32))"]
ENCRYPTION_KEY=[Generate new: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"]
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_EMAIL=noreply@pakjobs.com
SMTP_RECIPIENTS=admin@example.com
USER_AGENT=Mozilla/5.0 (compatible; PakJobsBot/1.0)
SCRAPE_DELAY_SECONDS=3
MAX_SCRAPE_PAGES=50
TIMEZONE=Asia/Karachi
```

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait for build and deployment (~10 minutes)
3. Check logs for any errors
4. Visit your app URL: `https://pakjobs-api.onrender.com`

### Step 6: Initialize Production Database
```bash
# Option A: Use Render Shell
# In Render dashboard → Shell tab
python scripts/init_db.py

# Option B: Local connection with external URL
psql [EXTERNAL_DATABASE_URL] < schema.sql
```

### Step 7: Verify Deployment
- [ ] Health check: `https://pakjobs-api.onrender.com/health`
- [ ] Home page loads
- [ ] Database connection works
- [ ] No errors in logs

## 📊 Post-Deployment

### Monitoring
- [ ] Check Render dashboard for errors
- [ ] Monitor memory usage (<512MB)
- [ ] Check database size (<1GB)
- [ ] Verify automated scraping runs at 3 AM

### Testing in Production
- [ ] Test job search functionality
- [ ] Verify API endpoints work
- [ ] Test CSV export
- [ ] Confirm email notifications arrive
- [ ] Check scraper logs

### Performance Optimization
- [ ] Enable database connection pooling
- [ ] Monitor query performance
- [ ] Check API response times
- [ ] Review scraper efficiency

## 🔧 Maintenance Tasks

### Daily
- [ ] Check scraper logs for errors
- [ ] Monitor job count growth
- [ ] Review email notifications

### Weekly
- [ ] Verify all 9 scrapers still functional
- [ ] Check for website structure changes
- [ ] Review error rates
- [ ] Database backup

### Monthly
- [ ] Update dependencies (if needed)
- [ ] Review and clean old jobs (90+ days)
- [ ] Analyze scraping patterns
- [ ] Performance optimization

## 🐛 Troubleshooting

### Build Fails on Render
**Problem**: Build timeout or failure

**Solutions**:
- Check build logs for specific error
- Verify requirements.txt is correct
- Ensure Python 3.12 in runtime.txt
- Try manual deploy from different branch

### Database Connection Issues
**Problem**: Can't connect to database

**Solutions**:
- Verify DATABASE_URL is correct
- Check database is running
- Ensure IP whitelist includes Render (if external DB)
- Check connection string format

### Scrapers Not Working
**Problem**: No jobs being scraped

**Solutions**:
- Check website is accessible
- Verify HTML selectors still valid
- Increase SCRAPE_DELAY_SECONDS
- Check robots.txt compliance
- Review error logs

### Out of Memory
**Problem**: App crashes due to memory

**Solutions**:
- Reduce worker count in Procfile
- Optimize database queries
- Limit concurrent scrapers
- Clean up old data

### Slow Performance
**Problem**: API responses slow

**Solutions**:
- Check database indexes exist
- Run ANALYZE on tables
- Enable query caching
- Optimize scraper logic

## 🔒 Security Hardening

### Production Security
- [ ] HTTPS enabled (automatic on Render)
- [ ] Environment variables secured
- [ ] Database credentials encrypted
- [ ] API rate limiting active
- [ ] No debug mode in production

### Regular Security Tasks
- [ ] Update dependencies monthly
- [ ] Rotate credentials quarterly
- [ ] Review access logs
- [ ] Monitor for suspicious activity

## 📈 Scaling Considerations

### When to Scale
- Database >800MB (approaching 1GB limit)
- >10,000 API requests/day
- Scraper timeouts increase
- Memory usage consistently >400MB

### Scaling Options
1. **Upgrade Render Plan** ($7/month for 512MB→1GB)
2. **Optimize Database**: Archive old jobs, improve indexes
3. **External Caching**: Add Redis for API responses
4. **Separate Scrapers**: Move to background workers

## ✨ Success Metrics

### Technical Metrics
- [ ] 95%+ scraper success rate
- [ ] <500ms API response time
- [ ] 99%+ uptime
- [ ] <2% error rate

### Business Metrics
- [ ] 50,000+ jobs in database
- [ ] 9/9 scrapers operational
- [ ] Daily scraping successful
- [ ] Email notifications working

## 📞 Support Resources

- **Documentation**: README.md, INSTALLATION.md
- **API Docs**: API_DOCUMENTATION.md
- **GitHub Issues**: Report bugs and issues
- **Logs**: Check Render dashboard and logs/ directory

## ✅ Final Checklist

Before going live:
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Production environment configured
- [ ] Database initialized
- [ ] Scrapers tested
- [ ] Email notifications tested
- [ ] API endpoints verified
- [ ] Monitoring enabled
- [ ] Backup strategy in place
- [ ] Support plan ready

---

## 🎉 Deployment Complete!

Once all items checked:
1. ✅ Application is live
2. ✅ Scrapers running automatically
3. ✅ Users can search jobs
4. ✅ API is accessible
5. ✅ Analytics available

**Congratulations on deploying PakJobs Aggregator!** 🚀

---

*Last Updated: January 2025*
