"""
Manual scraper execution script
Run scrapers from command line
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers import SCRAPERS

load_dotenv()


def run_scraper(site_name: str, mode: str = 'incremental'):
    """
    Run a specific scraper
    
    Args:
        site_name: Name of site to scrape
        mode: 'incremental' or 'full_refresh'
    """
    if site_name not in SCRAPERS:
        print(f"❌ Unknown scraper: {site_name}")
        print(f"Available scrapers: {', '.join(SCRAPERS.keys())}")
        return
    
    print(f"\n{'='*60}")
    print(f"Running {site_name} scraper - {mode} mode")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        scraper_class = SCRAPERS[site_name]
        scraper = scraper_class()
        stats = scraper.run(mode=mode)
        
        print(f"\n{'='*60}")
        print(f"Scraper completed successfully!")
        print(f"{'='*60}")
        print(f"Jobs found: {stats.get('jobs_found', 0)}")
        print(f"Jobs new: {stats.get('jobs_new', 0)}")
        print(f"Jobs updated: {stats.get('jobs_updated', 0)}")
        print(f"Jobs skipped: {stats.get('jobs_skipped', 0)}")
        print(f"Errors: {stats.get('errors', 0)}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Scraper failed: {e}")
        raise


def run_all_scrapers(mode: str = 'incremental'):
    """Run all scrapers sequentially"""
    print(f"\n{'='*60}")
    print(f"Running ALL scrapers - {mode} mode")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    results = {}
    
    for site_name in SCRAPERS.keys():
        print(f"\n▶ Starting {site_name}...")
        try:
            scraper_class = SCRAPERS[site_name]
            scraper = scraper_class()
            stats = scraper.run(mode=mode)
            results[site_name] = stats
            print(f"✅ {site_name}: {stats.get('jobs_new', 0)} new jobs")
        except Exception as e:
            print(f"❌ {site_name} failed: {e}")
            results[site_name] = {'error': str(e)}
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    total_new = sum(r.get('jobs_new', 0) for r in results.values())
    total_found = sum(r.get('jobs_found', 0) for r in results.values())
    total_errors = sum(r.get('errors', 0) for r in results.values())
    
    print(f"Total jobs found: {total_found}")
    print(f"Total new jobs: {total_new}")
    print(f"Total errors: {total_errors}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")


def main():
    """Parse arguments and run scrapers"""
    parser = argparse.ArgumentParser(description='Run PakJobs scrapers')
    
    parser.add_argument(
        '--site',
        type=str,
        help=f"Specific site to scrape. Options: {', '.join(SCRAPERS.keys())}, all"
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['incremental', 'full_refresh'],
        default='incremental',
        help='Scraping mode (default: incremental)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available scrapers'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable scrapers:")
        for site_name in SCRAPERS.keys():
            print(f"  - {site_name}")
        print()
        return
    
    if not args.site:
        print("Running all scrapers by default...")
        run_all_scrapers(args.mode)
    elif args.site == 'all':
        run_all_scrapers(args.mode)
    else:
        run_scraper(args.site, args.mode)


if __name__ == '__main__':
    main()
