-- Migration: Add Complete Job Fields
-- Date: 2025-10-16
-- Description: Add all missing fields from Rozee.pk job postings

-- Add new columns to jobs table
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS industry VARCHAR(100),
ADD COLUMN IF NOT EXISTS functional_area VARCHAR(100),
ADD COLUMN IF NOT EXISTS career_level VARCHAR(50),
ADD COLUMN IF NOT EXISTS job_shift VARCHAR(50),
ADD COLUMN IF NOT EXISTS total_positions INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS application_deadline DATE,
ADD COLUMN IF NOT EXISTS minimum_education VARCHAR(100),
ADD COLUMN IF NOT EXISTS degree_title VARCHAR(200),
ADD COLUMN IF NOT EXISTS minimum_experience VARCHAR(50),
ADD COLUMN IF NOT EXISTS age_range VARCHAR(50),
ADD COLUMN IF NOT EXISTS gender VARCHAR(20),
ADD COLUMN IF NOT EXISTS salary_currency VARCHAR(10) DEFAULT 'PKR',
ADD COLUMN IF NOT EXISTS salary_period VARCHAR(20),
ADD COLUMN IF NOT EXISTS company_logo_url TEXT,
ADD COLUMN IF NOT EXISTS company_profile_url TEXT,
ADD COLUMN IF NOT EXISTS external_job_id VARCHAR(50);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_jobs_industry ON jobs(industry);
CREATE INDEX IF NOT EXISTS idx_jobs_functional_area ON jobs(functional_area);
CREATE INDEX IF NOT EXISTS idx_jobs_career_level ON jobs(career_level);
CREATE INDEX IF NOT EXISTS idx_jobs_application_deadline ON jobs(application_deadline);
CREATE INDEX IF NOT EXISTS idx_jobs_minimum_education ON jobs(minimum_education);
CREATE INDEX IF NOT EXISTS idx_jobs_gender ON jobs(gender);
CREATE INDEX IF NOT EXISTS idx_jobs_external_id ON jobs(external_job_id);

-- Update comment on table
COMMENT ON COLUMN jobs.industry IS 'Job industry category (e.g., IT, Finance, Healthcare)';
COMMENT ON COLUMN jobs.functional_area IS 'Functional area/department (e.g., Software Development, Marketing)';
COMMENT ON COLUMN jobs.career_level IS 'Career level (e.g., Entry Level, Mid Level, Senior, Manager)';
COMMENT ON COLUMN jobs.job_shift IS 'Work shift (e.g., First Shift (Day), Second Shift, Night Shift)';
COMMENT ON COLUMN jobs.total_positions IS 'Number of open positions for this job';
COMMENT ON COLUMN jobs.application_deadline IS 'Last date to apply for this job';
COMMENT ON COLUMN jobs.minimum_education IS 'Minimum education level required';
COMMENT ON COLUMN jobs.degree_title IS 'Specific degree title required';
COMMENT ON COLUMN jobs.minimum_experience IS 'Minimum years of experience required';
COMMENT ON COLUMN jobs.age_range IS 'Age range requirement (e.g., 25-35 years)';
COMMENT ON COLUMN jobs.gender IS 'Gender requirement (Male/Female/No Preference)';
COMMENT ON COLUMN jobs.salary_currency IS 'Salary currency code';
COMMENT ON COLUMN jobs.salary_period IS 'Salary period (Month/Year/Hour)';
COMMENT ON COLUMN jobs.company_logo_url IS 'URL to company logo image';
COMMENT ON COLUMN jobs.company_profile_url IS 'URL to company profile page';
COMMENT ON COLUMN jobs.external_job_id IS 'External job ID from source site';
