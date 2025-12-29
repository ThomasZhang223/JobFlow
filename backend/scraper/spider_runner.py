"""
Spider Runner - Run Scrapy spiders programmatically
Used by Celery workers to scrape jobs
"""

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys
import os
import json

# Add indeed_scraper to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'indeed_scraper'))

from scraper.indeed_scraper.spiders.indeed_spider import IndeedSpider


def run_indeed_spider(query, location, max_results=50, output_file=None):
    """
    Run the Indeed spider and return scraped jobs
    
    Args:
        query (str): Job search query (e.g., "python developer")
        location (str): Location (e.g., "New York, NY")
        max_results (int): Maximum jobs to scrape (default: 50)
        output_file (str): Optional file to save results
    
    Returns:
        list: List of scraped job dictionaries
    
    Example:
        jobs = run_indeed_spider("python developer", "NYC", max_results=20)
        print(f"Scraped {len(jobs)} jobs")
    """
    
    # Get Scrapy settings from the project
    settings = get_project_settings()
    settings.set('SPIDER_MODULES', ['indeed_scraper.spiders'])
    settings.set('NEWSPIDER_MODULE', 'indeed_scraper.spiders')
    
    # Override settings for programmatic use
    settings.set('LOG_LEVEL', 'INFO')
    
    # Disable file output if not specified (we'll collect in memory)
    if output_file:
        settings.set('FEED_FORMAT', 'json')
        settings.set('FEED_URI', output_file)
    
    # Create crawler process
    process = CrawlerProcess(settings)
    
    # Storage for scraped items
    scraped_items = []
    
    # Signal handler to collect items
    def collect_items(item, response, spider):
        scraped_items.append(dict(item))
    
    # Connect signal
    from scrapy import signals
    from scrapy.signalmanager import dispatcher
    dispatcher.connect(collect_items, signal=signals.item_scraped)
    
    # Add spider to process with arguments
    process.crawl(
        IndeedSpider,
        query=query,
        location=location,
        max_results=max_results
    )
    
    # Run spider (blocks until complete)
    process.start()
    
    print(f"\n✅ Scraping complete! Found {len(scraped_items)} jobs")
    
    if output_file:
        print(f"📁 Results saved to: {output_file}")
    
    return scraped_items


def run_spider_subprocess(query, location, max_results=50, output_file='jobs.json'):
    """
    Alternative method: Run spider in subprocess
    Useful if you need to run multiple spiders sequentially
    
    Args:
        query (str): Job search query
        location (str): Location
        max_results (int): Maximum results
        output_file (str): Output filename
    
    Returns:
        list: Scraped jobs from the output file
    """
    import subprocess
    import tempfile
    
    if not output_file:
        output_file = tempfile.mktemp(suffix='.json')
    
    # Build command
    cmd = [
        'scrapy', 'crawl', 'indeed',
        '-a', f'query={query}',
        '-a', f'location={location}',
        '-a', f'max_results={max_results}',
        '-o', output_file
    ]
    
    # Run spider as subprocess
    result = subprocess.run(
        cmd,
        cwd=os.path.join(os.path.dirname(__file__), 'indeed_scraper'),
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    if result.returncode != 0:
        raise Exception(f"Spider failed: {result.stderr}")
    
    # Read results
    with open(output_file, 'r') as f:
        jobs = json.load(f)
    
    return jobs


# Example usage and testing
if __name__ == '__main__':
    import sys
    
    # Get arguments or use defaults
    query = sys.argv[1] if len(sys.argv) > 1 else "python developer"
    location = sys.argv[2] if len(sys.argv) > 2 else "New York"
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    print(f"🕷️  Starting Indeed Spider...")
    print(f"   Query: {query}")
    print(f"   Location: {location}")
    print(f"   Max Results: {max_results}")
    print()
    
    # Run spider
    jobs = run_indeed_spider(
        query=query,
        location=location,
        max_results=max_results,
        output_file='indeed_jobs.json'
    )
    
    # Display results
    print(f"\n📊 Results Summary:")
    print(f"   Total jobs scraped: {len(jobs)}")
    
    if jobs:
        print(f"\n📋 Sample job:")
        sample = jobs[0]
        print(f"   Title: {sample.get('title')}")
        print(f"   Company: {sample.get('company_name')}")
        print(f"   Location: {sample.get('location')}")
        if sample.get('salary_text'):
            print(f"   Salary: {sample.get('salary_text')}")
        print(f"   URL: {sample.get('application_url')}")
    
    print(f"\n✅ Done! Check indeed_jobs.json for full results")