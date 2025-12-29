import scrapy
from indeed_scraper.items import JobItem
from datetime import datetime
from urllib.parse import urlencode
import json


class IndeedSpider(scrapy.Spider):
    """
    Spider to scrape job listings from Indeed.com
    Based on: https://github.com/python-scrapy-playbook/indeed-python-scrapy-scraper
    """
    
    name = 'indeed'
    allowed_domains = ['indeed.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'RETRY_TIMES': 3,
    }
    
    def __init__(self, query='python developer', location='New York', max_results=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.location = location
        self.max_results = int(max_results)
        self.jobs_scraped = 0
        self.start_page = 0
        
        self.logger.info(f"=== Indeed Spider Initialized ===")
        self.logger.info(f"Query: {self.query}")
        self.logger.info(f"Location: {self.location}")
        self.logger.info(f"Max Results: {self.max_results}")
    
    def start_requests(self):
        """Generate initial request to Indeed"""
        url = self.get_indeed_search_url(self.query, self.location, self.start_page)
        
        self.logger.info(f"Starting URL: {url}")
        
        yield scrapy.Request(
            url=url,
            callback=self.parse_search_results,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    {
                        'method': 'wait_for_load_state',
                        'args': ['networkidle'],
                        'kwargs': {'timeout': 30000}
                    }
                ]
            },
            errback=self.handle_error
        )
    
    def parse_search_results(self, response):
        """Parse Indeed search results page"""
        
        self.logger.info(f"Parsing page: {response.url}")
        self.logger.info(f"Response status: {response.status}")
        
        # Extract job cards - try multiple selectors
        job_cards = response.css('div.job_seen_beacon')
        
        if not job_cards:
            job_cards = response.css('td.resultContent')
        
        if not job_cards:
            job_cards = response.css('div.cardOutline')
        
        self.logger.info(f"Found {len(job_cards)} job cards")
        
        if len(job_cards) == 0:
            self.logger.warning("No job cards found!")
            # Save HTML for debugging
            with open('debug_page.html', 'w') as f:
                f.write(response.text)
            self.logger.info("Saved HTML to debug_page.html for inspection")
        
        # Process each job card
        for card in job_cards:
            if self.jobs_scraped >= self.max_results:
                self.logger.info(f"Reached max limit: {self.max_results}")
                return
            
            job_data = self.parse_job_card(card, response)
            
            if job_data:
                self.jobs_scraped += 1
                yield job_data
        
        # Handle pagination
        if self.jobs_scraped < self.max_results:
            next_page_url = self.get_next_page_url(response)
            if next_page_url:
                self.logger.info(f"Following next page: {next_page_url}")
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_search_results,
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_page_methods': [
                            {
                                'method': 'wait_for_load_state',
                                'args': ['networkidle'],
                                'kwargs': {'timeout': 30000}
                            }
                        ]
                    },
                    errback=self.handle_error
                )
            else:
                self.logger.info("No more pages found")
    
    def parse_job_card(self, card, response):
        """Extract job data from a job card"""
        
        try:
            # Job ID - try multiple locations
            job_id = (
                card.css('::attr(data-jk)').get() or
                card.css('a::attr(data-jk)').get() or
                card.css('h2 a::attr(data-jk)').get()
            )
            
            # Job title
            title = (
                card.css('h2.jobTitle span[title]::attr(title)').get() or
                card.css('h2.jobTitle span::text').get() or
                card.css('a[data-jk] span[title]::attr(title)').get()
            )
            
            # Company name
            company = (
                card.css('span[data-testid="company-name"]::text').get() or
                card.css('span.companyName::text').get() or
                card.css('span.companyName a::text').get()
            )
            
            # Location
            location = (
                card.css('div[data-testid="text-location"]::text').get() or
                card.css('div.companyLocation::text').get()
            )
            
            # Salary
            salary = (
                card.css('div.metadata div.salary-snippet-container::text').get() or
                card.css('div.salary-snippet-container::text').get()
            )
            
            # Job type
            job_type = (
                card.css('div.metadata div.attribute_snippet::text').get() or
                card.css('span.attribute_snippet::text').get()
            )
            
            # Description snippet
            description = card.css('div.job-snippet::text').get()
            
            # Build job URL
            if job_id:
                job_url = f"https://www.indeed.com/viewjob?jk={job_id}"
            else:
                job_link = card.css('h2.jobTitle a::attr(href)').get()
                if job_link:
                    if job_link.startswith('http'):
                        job_url = job_link
                    elif job_link.startswith('/'):
                        job_url = f"https://www.indeed.com{job_link}"
                    else:
                        job_url = f"https://www.indeed.com/{job_link}"
                else:
                    job_url = response.url
            
            # Validate required fields
            if not job_id or not title or not company:
                self.logger.debug(f"Skipping incomplete job: id={job_id}, title={title}, company={company}")
                return None
            
            # Create JobItem
            job = JobItem()
            job['external_id'] = job_id.strip()
            job['title'] = title.strip()
            job['company_name'] = company.strip()
            job['location'] = location.strip() if location else ''
            job['salary_text'] = salary.strip() if salary else None
            job['job_type'] = job_type.strip() if job_type else None
            job['description'] = description.strip() if description else None
            job['application_url'] = job_url
            job['posted_date'] = None
            job['search_query'] = self.query
            job['search_location'] = self.location
            job['scraped_at'] = datetime.utcnow().isoformat()
            
            self.logger.info(f"✓ Scraped job {self.jobs_scraped + 1}: {title} at {company}")
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")
            return None
    
    def get_indeed_search_url(self, query, location, page=0):
        """Build Indeed search URL"""
        params = {
            'q': query,
            'l': location,
            'start': page * 10  # Indeed shows 10 jobs per page
        }
        return f"https://www.indeed.com/jobs?{urlencode(params)}"
    
    def get_next_page_url(self, response):
        """Extract next page URL from pagination"""
        
        # Try multiple pagination selectors
        next_link = (
            response.css('a[data-testid="pagination-page-next"]::attr(href)').get() or
            response.css('a[aria-label="Next Page"]::attr(href)').get() or
            response.css('nav[role="navigation"] a[data-testid="pagination-page-next"]::attr(href)').get()
        )
        
        if next_link:
            if next_link.startswith('http'):
                return next_link
            elif next_link.startswith('/'):
                return f"https://www.indeed.com{next_link}"
            else:
                return f"https://www.indeed.com/{next_link}"
        
        return None
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info(f"=== Spider Closed ===")
        self.logger.info(f"Reason: {reason}")
        self.logger.info(f"Total jobs scraped: {self.jobs_scraped}")