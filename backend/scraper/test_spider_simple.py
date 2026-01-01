#!/usr/bin/env python3
"""
Simple spider test without Redis/settings dependencies
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the scraper directory to Python path
script_dir = Path(__file__).parent
scraper_dir = script_dir / 'indeed_scraper'
sys.path.insert(0, str(scraper_dir))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_simple_test(preferences_json, max_results=5):
    """Test spider with minimal setup"""

    # Change to scrapy project directory
    os.chdir(scraper_dir)

    # Get Scrapy settings
    settings = get_project_settings()
    settings.set('LOG_LEVEL', 'INFO')

    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name

    settings.set('FEED_FORMAT', 'json')
    settings.set('FEED_URI', output_file)

    # Parse preferences
    preferences = json.loads(preferences_json)

    # Create a simple spider class without Redis dependencies
    from scrapy.spiders import Spider
    import scrapy
    from urllib.parse import urlencode
    from datetime import datetime

    class SimpleIndeedSpider(Spider):
        name = 'simple_indeed'
        allowed_domains = ['indeed.com']

        custom_settings = {
            'DOWNLOAD_DELAY': 1,
            'CONCURRENT_REQUESTS': 1,
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            'RETRY_TIMES': 2,
        }

        def __init__(self, preferences=None, max_results=5):
            super().__init__()

            if isinstance(preferences, str):
                preferences = json.loads(preferences)

            self.query = preferences['title']
            self.location = preferences['location']
            self.max_results = int(max_results)
            self.jobs_scraped = 0
            self.pages_visited = 0
            self.max_pages = 3  # Limit to 3 pages for testing

        def start_requests(self):
            url = f"https://www.indeed.com/jobs?{urlencode({'q': self.query, 'l': self.location})}"
            yield scrapy.Request(url=url, callback=self.parse)

        def parse(self, response):
            self.pages_visited += 1
            self.logger.info(f"Parsing page {self.pages_visited}: {response.url}")

            if self.pages_visited > self.max_pages:
                self.logger.info(f"Reached max pages ({self.max_pages})")
                return

            # Simple job extraction (without complex filtering)
            job_cards = response.css('div.job_seen_beacon')
            if not job_cards:
                job_cards = response.css('td.resultContent')

            self.logger.info(f"Found {len(job_cards)} job cards")

            for card in job_cards:
                if self.jobs_scraped >= self.max_results:
                    return

                title = card.css('h2.jobTitle span::text').get() or card.css('h2.jobTitle span::attr(title)').get()
                company = card.css('span[data-testid="company-name"]::text').get()

                if title and company:
                    yield {
                        'title': title.strip(),
                        'company': company.strip(),
                        'scraped_at': datetime.now().isoformat()
                    }
                    self.jobs_scraped += 1
                    self.logger.info(f"Scraped job {self.jobs_scraped}: {title}")

    # Create crawler process
    process = CrawlerProcess(settings)

    # Run spider
    process.crawl(SimpleIndeedSpider, preferences=preferences, max_results=max_results)
    process.start()

    # Read results
    jobs = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            content = f.read().strip()
            if content:
                jobs = json.loads(content)
        os.unlink(output_file)  # Clean up

    return jobs

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python test_spider_simple.py '<preferences_json>' <max_results>")
        sys.exit(1)

    preferences_json = sys.argv[1]
    max_results = int(sys.argv[2])

    print(f"Testing simple spider with: {preferences_json}")
    jobs = run_simple_test(preferences_json, max_results)

    print(f"\nResults: {len(jobs)} jobs found")
    for job in jobs:
        print(f"- {job['title']} at {job['company']}")