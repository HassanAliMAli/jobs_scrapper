-- =============================================================================
-- PAKJOBS AGGREGATOR - DATABASE SCHEMA
-- =============================================================================
-- PostgreSQL 16 Schema
-- Designed for 1GB free tier on Render.com
-- Expected storage: ~500MB for 50,000 jobs

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- =============================================================================
-- TABLE: jobs (Main job listings table)
-- =============================================================================
CREATE TABLE IF NOT EXISTS jobs (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source Information
    site_source VARCHAR(50) NOT NULL CHECK (site_source IN (
        'rozee', 'mustakbil', 'indeed', 'brightspyre', 'bayt',
        'jobz', 'bayrozgar', 'jobsalert', 'pakpositions'
    )),
    source_url TEXT NOT NULL UNIQUE,  -- Original job URL
    
    -- Job Details
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(50) DEFAULT 'Pakistan',
    
    -- Salary Information
    salary_text TEXT,
    salary_min INTEGER CHECK (salary_min >= 0),
    salary_max INTEGER CHECK (salary_max >= salary_min),
    salary_currency VARCHAR(10) DEFAULT 'PKR',
    
    -- Job Content
    description TEXT,
    requirements TEXT,
    benefits TEXT,
    
    -- Skills & Qualifications (JSONB for flexibility)
    skills JSONB DEFAULT '[]'::jsonb,
    experience_level VARCHAR(50),
    experience_years VARCHAR(50),
    education VARCHAR(255),
    
    -- Job Type & Work Mode
    job_type VARCHAR(50),
    is_remote BOOLEAN DEFAULT false,
    is_hybrid BOOLEAN DEFAULT false,
    is_onsite BOOLEAN DEFAULT true,
    
    -- Application Details
    application_method VARCHAR(20) CHECK (application_method IN ('email', 'url', 'unknown')),
    application_email VARCHAR(255),
    application_url TEXT,
    deadline_date DATE,
    
    -- Dates
    posted_date DATE,
    scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Status Flags
    is_active BOOLEAN DEFAULT true,
    is_duplicate BOOLEAN DEFAULT false,
    duplicate_of UUID REFERENCES jobs(id) ON DELETE SET NULL,
    
    -- Constraints
    CHECK (NOT (is_remote AND is_onsite AND NOT is_hybrid))
);

-- =============================================================================
-- INDEXES FOR jobs TABLE
-- =============================================================================

-- Primary search indexes
CREATE INDEX idx_jobs_site_source ON jobs(site_source);
CREATE INDEX idx_jobs_city ON jobs(city) WHERE city IS NOT NULL;
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_scraped_at ON jobs(scraped_at DESC);
CREATE INDEX idx_jobs_active ON jobs(is_active) WHERE is_active = true;

-- Salary range index
CREATE INDEX idx_jobs_salary_range ON jobs(salary_min, salary_max) 
WHERE salary_min IS NOT NULL;

-- Full-text search index (GIN - critical for performance)
CREATE INDEX idx_jobs_fulltext ON jobs USING GIN(
    to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(description, '') || ' ' ||
        COALESCE(company, '')
    )
);

-- JSONB skills index
CREATE INDEX idx_jobs_skills ON jobs USING GIN(skills jsonb_path_ops);

-- Composite index for common query pattern
CREATE INDEX idx_jobs_active_posted ON jobs(is_active, posted_date DESC) 
WHERE is_active = true;

-- Duplicate detection index
CREATE INDEX idx_jobs_duplicate ON jobs(is_duplicate) WHERE is_duplicate = true;

-- =============================================================================
-- TABLE: scrape_logs (Monitoring and tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS scrape_logs (
    id SERIAL PRIMARY KEY,
    
    -- Scraper Information
    site_name VARCHAR(50) NOT NULL,
    scrape_mode VARCHAR(20) NOT NULL CHECK (scrape_mode IN ('incremental', 'full_refresh')),
    
    -- Timing
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Results
    jobs_found INTEGER DEFAULT 0,
    jobs_new INTEGER DEFAULT 0,
    jobs_updated INTEGER DEFAULT 0,
    jobs_skipped INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for scrape_logs
CREATE INDEX idx_scrape_logs_site ON scrape_logs(site_name, start_time DESC);
CREATE INDEX idx_scrape_logs_status ON scrape_logs(status, start_time DESC);
CREATE INDEX idx_scrape_logs_date ON scrape_logs(start_time DESC);

-- =============================================================================
-- TABLE: user_config (System configuration)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_config (
    id SERIAL PRIMARY KEY,
    
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    description TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for config lookups
CREATE UNIQUE INDEX idx_config_key ON user_config(config_key);

-- =============================================================================
-- TABLE: analytics_cache (Pre-computed analytics)
-- =============================================================================
CREATE TABLE IF NOT EXISTS analytics_cache (
    id SERIAL PRIMARY KEY,
    
    metric_name VARCHAR(100) NOT NULL UNIQUE,
    metric_value JSONB NOT NULL,
    
    computed_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    CONSTRAINT analytics_cache_metric_key UNIQUE (metric_name)
);

-- Index for analytics retrieval
CREATE UNIQUE INDEX idx_analytics_metric ON analytics_cache(metric_name);
CREATE INDEX idx_analytics_expiry ON analytics_cache(expires_at);

-- =============================================================================
-- DEFAULT CONFIGURATION VALUES
-- =============================================================================
INSERT INTO user_config (config_key, config_value, is_encrypted, description) VALUES
('scrape_schedule', '0 3 * * *', false, 'Cron expression for daily scraping (3 AM PKT)'),
('email_recipients', '', false, 'Comma-separated email list for notifications'),
('external_db_enabled', 'false', false, 'Enable external database push'),
('external_db_type', 'postgresql', false, 'Database type: postgresql, mysql, mongodb'),
('external_db_connection', '', true, 'Encrypted connection string'),
('max_scrape_pages', '50', false, 'Maximum pages per site to prevent infinite loops'),
('scrape_delay_seconds', '3', false, 'Delay between requests (politeness)'),
('incremental_mode', 'true', false, 'Enable incremental scraping by default'),
('data_retention_days', '90', false, 'Archive jobs after this many days')
ON CONFLICT (config_key) DO NOTHING;

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Auto-update last_updated timestamp on jobs
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_jobs_last_updated 
    BEFORE UPDATE ON jobs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_last_updated_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active jobs view (most commonly queried)
CREATE OR REPLACE VIEW active_jobs AS
SELECT 
    id, title, company, location, city,
    salary_min, salary_max, salary_text,
    description, skills, experience_level,
    job_type, is_remote, is_hybrid,
    posted_date, source_url, site_source
FROM jobs
WHERE is_active = true
ORDER BY posted_date DESC;

-- Recent scrape status view
CREATE OR REPLACE VIEW recent_scrapes AS
SELECT 
    site_name,
    status,
    jobs_found,
    jobs_new,
    duration_seconds,
    start_time,
    error_message
FROM scrape_logs
WHERE start_time >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY start_time DESC;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================
COMMENT ON TABLE jobs IS 'Main table storing all scraped job listings';
COMMENT ON TABLE scrape_logs IS 'Monitoring table tracking each scrape execution';
COMMENT ON TABLE user_config IS 'System configuration and settings';
COMMENT ON TABLE analytics_cache IS 'Cached analytics for dashboard performance';

COMMENT ON COLUMN jobs.skills IS 'JSONB array of required skills, e.g. ["Python", "SQL"]';
COMMENT ON COLUMN jobs.is_duplicate IS 'True if job is cross-posted on multiple sites';
COMMENT ON COLUMN jobs.duplicate_of IS 'References original job if this is a duplicate';

-- =============================================================================
-- SCHEMA VERSION
-- =============================================================================
INSERT INTO user_config (config_key, config_value, description) VALUES
('schema_version', '1.0.0', 'Database schema version')
ON CONFLICT (config_key) DO UPDATE SET config_value = '1.0.0';
