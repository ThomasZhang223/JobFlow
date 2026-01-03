#!/usr/bin/env python3
"""
Standalone spider runner script
This script can be called from Celery to run the Indeed spider
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the scraper directory to Python path
script_dir = Path(__file__).parent
scraper_dir = script_dir / 'indeed_scraper'
backend_dir = script_dir.parent  # Go up to backend/ directory

sys.path.insert(0, str(backend_dir))  # For app.* imports
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(scraper_dir))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from indeed_scraper.spiders.indeed_spider import IndeedSpider

def run_spider_standalone(preferences_json):
    """
    Run the spider standalone and return scraped jobs

    Args:
        preferences_json: JSON string of user preferences

    Returns:
        None (jobs saved directly to database)
    """

    try:
        # Change to scrapy project directory
        os.chdir(scraper_dir)

        # Get Scrapy settings
        settings = get_project_settings()

        # Disable feed output since we save directly to database
        # Just need to ensure clean stdout
        settings.set('FEEDS', {})  # No output feeds

        # Parse preferences
        preferences = json.loads(preferences_json)

        # Create crawler process
        process = CrawlerProcess(settings)

        # Run spider
        process.crawl(
            IndeedSpider,
            preferences=preferences
        )

        process.start()

    except Exception as e:
        print(f"Error in run_spider_standalone: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python run_spider.py '<preferences_json>'")
        sys.exit(1)

    preferences_json = sys.argv[1]

    # Run spider - jobs are saved directly to database, no output needed
    run_spider_standalone(preferences_json)