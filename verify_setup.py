#!/usr/bin/env python
"""
Setup Verification Script
Run this to verify your PakJobs Aggregator installation
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_mark():
    return f"{GREEN}✓{RESET}"


def cross_mark():
    return f"{RED}✗{RESET}"


def warning_mark():
    return f"{YELLOW}⚠{RESET}"


def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print(f"{check_mark()} Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"{cross_mark()} Python 3.12+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def check_required_files():
    """Check if all required files exist"""
    print("\nChecking required files...")
    
    required_files = [
        'app.py',
        'schema.sql',
        'requirements.txt',
        '.env.example',
        'Procfile',
        'render.yaml',
        'runtime.txt',
        'scrapers/__init__.py',
        'scrapers/base.py',
        'data_pipeline/__init__.py',
        'templates/base.html',
        'scripts/init_db.py',
        'scripts/run_scrapers.py',
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"{check_mark()} {file}")
        else:
            print(f"{cross_mark()} {file} - MISSING")
            all_exist = False
    
    return all_exist


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\nChecking environment configuration...")
    
    if not Path('.env').exists():
        print(f"{warning_mark()} .env file not found")
        print(f"  → Run: cp .env.example .env")
        return False
    
    print(f"{check_mark()} .env file exists")
    
    # Check for required variables
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'ENCRYPTION_KEY',
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in env_content or f"{var}=your-" in env_content or f"{var}=" in env_content and len(env_content.split(f"{var}=")[1].split('\n')[0].strip()) < 10:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"{warning_mark()} Missing or incomplete variables: {', '.join(missing_vars)}")
        return False
    else:
        print(f"{check_mark()} All required environment variables set")
        return True


def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking Python dependencies...")
    
    required_packages = [
        'flask',
        'scrapy',
        'playwright',
        'psycopg2',
        'pandas',
        'apscheduler',
        'cryptography',
        'dotenv',
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"{check_mark()} {package}")
        except ImportError:
            print(f"{cross_mark()} {package} - NOT INSTALLED")
            all_installed = False
    
    if not all_installed:
        print(f"\n{warning_mark()} Run: pip install -r requirements.txt")
    
    return all_installed


def check_database_connection():
    """Check database connection"""
    print("\nChecking database connection...")
    
    try:
        from dotenv import load_dotenv
        import psycopg2
        
        load_dotenv()
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print(f"{cross_mark()} DATABASE_URL not set in .env")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'jobs'
        """)
        
        if cursor.fetchone()[0] > 0:
            print(f"{check_mark()} Database connected and initialized")
            
            # Get job count
            cursor.execute("SELECT COUNT(*) FROM jobs")
            job_count = cursor.fetchone()[0]
            print(f"  → Jobs in database: {job_count}")
        else:
            print(f"{warning_mark()} Database connected but not initialized")
            print(f"  → Run: python scripts/init_db.py")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        print(f"{cross_mark()} psycopg2 not installed")
        return False
    except Exception as e:
        print(f"{cross_mark()} Database connection failed: {e}")
        print(f"  → Check DATABASE_URL in .env")
        print(f"  → Ensure PostgreSQL is running")
        return False


def check_scrapers():
    """Check if scrapers can be imported"""
    print("\nChecking scrapers...")
    
    try:
        from scrapers import SCRAPERS
        
        print(f"{check_mark()} Found {len(SCRAPERS)} scrapers:")
        for name in SCRAPERS.keys():
            print(f"  → {name}")
        
        return True
    except Exception as e:
        print(f"{cross_mark()} Failed to import scrapers: {e}")
        return False


def check_playwright():
    """Check if Playwright browsers are installed"""
    print("\nChecking Playwright browsers...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print(f"{check_mark()} Chromium browser installed")
                return True
            except Exception:
                print(f"{warning_mark()} Chromium browser not found")
                print(f"  → Run: playwright install chromium")
                return False
    except ImportError:
        print(f"{cross_mark()} Playwright not installed")
        return False


def main():
    """Run all checks"""
    print_header("PakJobs Aggregator - Setup Verification")
    
    checks = {
        "Python Version": check_python_version(),
        "Required Files": check_required_files(),
        "Environment Configuration": check_env_file(),
        "Python Dependencies": check_dependencies(),
        "Database Connection": check_database_connection(),
        "Scrapers": check_scrapers(),
        "Playwright Browsers": check_playwright(),
    }
    
    print_header("Verification Summary")
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check_name, result in checks.items():
        status = check_mark() if result else cross_mark()
        print(f"{status} {check_name}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    
    if passed == total:
        print(f"{GREEN}✓ All checks passed! ({passed}/{total}){RESET}")
        print(f"\n{GREEN}Your PakJobs Aggregator is ready to use!{RESET}")
        print(f"\nNext steps:")
        print(f"  1. Run application: python app.py")
        print(f"  2. Open browser: http://localhost:5000")
        print(f"  3. Run scrapers: python scripts/run_scrapers.py --site rozee")
    else:
        print(f"{YELLOW}⚠ {passed}/{total} checks passed{RESET}")
        print(f"\n{YELLOW}Please fix the issues above before running the application.{RESET}")
    
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return passed == total


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Verification cancelled by user.{RESET}")
        sys.exit(1)
