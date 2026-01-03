import scrapy
import math
import os
import sys
from datetime import datetime
from urllib.parse import urlencode
import json

# Import anti-bot measures
from indeed_scraper.user_agents import get_random_user_agent
from indeed_scraper.proxies import get_random_proxy, is_proxy_enabled

# Add paths for imports
current_dir = os.path.dirname(__file__)
backend_dir = os.path.join(current_dir, '..')

# Add backend directory to path for app imports
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from indeed_scraper.items import JobItem

# Redis publishing in subprocess via environment variables
def publish_update(message):
    """Publish scrape update to Redis for real-time frontend updates"""
    try:
        import redis

        # Read Redis settings from environment variables
        redis_url = os.environ.get('REDIS_URL')
        scrape_update_channel = os.environ.get('SCRAPE_UPDATE_CHANNEL')

        if not redis_url or not scrape_update_channel:
            print(f'No Redis connection available')
            return

        r = redis.from_url(redis_url)

        message_json = json.dumps(message)

        r.publish(scrape_update_channel, message_json)
        r.close()

    except Exception as e:
        # Don't fail spider if Redis publishing fails
        print(f"Redis publishing failed: {e}")
        pass

class IndeedSpider(scrapy.Spider):
    """
    Spider to scrape job listings from Indeed.com
    Based on: https://github.com/python-scrapy-playbook/indeed-python-scrapy-scraper
    """
    
    name = 'indeed'
    base_domain = 'ca.indeed.com'
    allowed_domains = [base_domain]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,  # Much faster with high concurrency
        'CONCURRENT_REQUESTS': 32,  # High total concurrency for scalability
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,  # Max 16 to Indeed simultaneously
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'RETRY_TIMES': 3,
        'AUTOTHROTTLE_ENABLED': True,  # Auto-adjust based on server response
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 8.0,  # Target 8 concurrent per domain
        'AUTOTHROTTLE_DEBUG': False,  # Set to True for debugging throttling
        'LOG_LEVEL': 'INFO',  # Reduce verbosity while keeping important logs

        # Anti-bot measures
        'ROBOTSTXT_OBEY': False,  # Ignore robots.txt for scraping
        'COOKIES_ENABLED': False,  # Better anonymity without session tracking
        'TELNETCONSOLE_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-CA,en-US;q=0.9,en;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Priority': 'u=0, i',
            'Referer': 'https://www.google.com/',
        }
    }
    
    def __init__(self, preferences=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize query, preference, tallying variables
        self.scrape_session_counted = False  # Track if we've incremented total_scrapes for this session

        # Handle both programmatic (dict) and command line (JSON string) calls
        if preferences is None:
            raise ValueError("preferences parameter is required")

        if isinstance(preferences, str):
            import json
            try:
                preferences = json.loads(preferences)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in preferences parameter: {e}")

        # Validate required preferences
        if not preferences.get('title') or not preferences.get('location'):
            raise ValueError("preferences must contain 'title' and 'location' fields")

        # Extract search parameters from user preferences
        # Use first title as primary search query
        title_prefs = preferences['title'].split(',')
        self.query = title_prefs[0].strip()

        # Use first location as primary search location
        location_prefs = preferences['location'].split(',')
        self.location = location_prefs[0].strip()

        # Store all preferences as lists for filtering - handle null/empty values
        self.preferred_titles = [t.strip().lower() for t in title_prefs]
        self.preferred_locations = [l.strip().lower() for l in location_prefs]
        
        # Handle company_name - check for null, empty, or 'null' string
        company_name_val = preferences.get('company_name')
        self.preferred_company_name = None
        if company_name_val and company_name_val != 'null' and str(company_name_val).strip():
            # Filters out any potential empty strings after splitting (if c.strip())
            self.preferred_company_name = [c.strip().lower() for c in str(company_name_val).split(',') if c.strip()]
            
        # Handle job_type - check for null, empty, or 'null' string
        job_type_val = preferences.get('job_type')
        self.preferred_job_types = None
        if job_type_val and job_type_val != 'null' and str(job_type_val).strip():
            # Filters out any potential empty strings after splitting (if j.strip())
            self.preferred_job_types = [j.strip().lower() for j in str(job_type_val).split(',') if j.strip()]

        # Handle salary - check for null, empty, or 'null' string
        salary_val = preferences.get('salary')
        self.preferred_salaries = None
        if salary_val and salary_val != 'null' and str(salary_val).strip():
            # Filters out any potential empty strings after splitting (if s.strip())
            self.preferred_salaries = [s.strip().lower() for s in str(salary_val).split(',') if s.strip()]

        # Handle description - check for null, empty, or 'null' string
        desc_val = preferences.get('description')
        self.preferred_descriptions = None
        if desc_val and desc_val != 'null' and str(desc_val).strip():
            # Filters out any potential empty strings after splitting (if d.strip())
            self.preferred_descriptions = [d.strip().lower() for d in str(desc_val).split(',') if d.strip()]

        # Handle benefits - check for null, empty, or 'null' string
        benefits_val = preferences.get('benefits')
        self.preferred_benefits = None
        if benefits_val and benefits_val != 'null' and str(benefits_val).strip():
            # Filters out any potential empty strings after splitting (if b.strip())
            self.preferred_benefits = [b.strip().lower() for b in str(benefits_val).split(',') if b.strip()]

        # Handle radius - check for null, empty, or 'null' string
        radius_val = preferences.get('radius')
        self.radius = None
        if radius_val and radius_val != 'null' and str(radius_val).strip():
            try:
                self.radius = int(radius_val)
            except (ValueError, TypeError):
                self.radius = None

        self.max_results = int(preferences['scrape_length'])
        self.jobs_scraped = 0
        self.pages_visited = 0
        self.max_pages = 15  # Safety limit - never visit more than 15 pages

        self.logger.info(f"=== Indeed Spider Initialized ===")
        self.logger.info(f"Primary Query: {self.query}")
        self.logger.info(f"Primary Location: {self.location}")
        self.logger.info(f"Location Radius: {self.radius}")
        self.logger.info(f"Max Results: {self.max_results}")
        self.logger.info(f"Title Filters: {self.preferred_titles}")
        self.logger.info(f"Location Filters: {self.preferred_locations}")
        self.logger.info(f"Job Type Filters: {self.preferred_job_types}")
        self.logger.info(f"Salary Filters: {self.preferred_salaries}")
        self.logger.info(f"Description Filters: {self.preferred_descriptions}")
    
    def start_requests(self):
        """Generate parallel requests to multiple pages simultaneously to bypass anti-bot detection"""
        # Calculate how many pages we might need based on max_results
        # Assume ~10-16 jobs per page, so we need roughly max_results/13 pages
        estimated_pages_needed = min(max(1, math.ceil(self.max_results/13)), self.max_pages)

        self.logger.info(f"=== PARALLEL PAGE LOADING STRATEGY ===")
        self.logger.info(f"Max results: {self.max_results}, Estimated pages needed: {estimated_pages_needed}")

        # Generate URLs for multiple pages simultaneously
        for page_num in range(estimated_pages_needed):
            page_url = self.get_indeed_search_url(page_num)

            self.logger.info(f"Queuing page {page_num + 1}: {page_url}")

            request = self.make_request(
                url=page_url,
                callback=self.parse_search_results_parallel,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_goto_kwargs': {'wait_until': 'domcontentloaded', 'timeout': 60000},
                    'page_number': page_num + 1,
                    'is_parallel_load': True
                },
                errback=self.handle_error,
                dont_filter=True
            )

            self.logger.info(f"Request created for page {page_num + 1}, yielding...")
            yield request

    def make_request(self, url, callback, **kwargs):
        """Create a request object with anti-bot measures (rotating user agents and proxies)"""
        headers = {}

        # Add rotating user agent
        user_agent = get_random_user_agent()
        headers['User-Agent'] = user_agent
        self.logger.info(f"Using user agent: {user_agent}...")

        # Create request with custom headers
        request = scrapy.Request(
            url=url,
            callback=callback,
            headers=headers,
            **kwargs
        )

        # Add proxy if available
        if is_proxy_enabled:
            proxy = get_random_proxy()
            request.meta['proxy'] = proxy
            self.logger.info(f"Using proxy: {proxy[:20]}...")

        return request
    
    def get_indeed_search_url(self, page, external_id=None):
        """Build Indeed search URL"""
        params = {
            'q': self.query,
            'l': self.location,
            'start': page * 10  # Indeed shows 10 jobs per page
        }

        # Add radius parameter if specified
        if self.radius is not None:
            params['radius'] = self.radius

        if external_id is not None:
            params['vjk'] = external_id
            
        return f"https://{self.base_domain}/jobs?{urlencode(params)}"
    
    def parse_search_results_parallel(self, response):
        """Parse search results for parallel loading strategy"""
        page_num = response.meta.get('page_number')

        # Increment pages visited counter for every page processed
        self.pages_visited += 1

        self.logger.info(f"=== PARSING PARALLEL PAGE {page_num} ===")
        self.logger.info(f"URL: {response.url}")
        self.logger.info(f"Response status: {response.status}")
        self.logger.info(f"Page title: {response.css('title::text').get()}")

        # Find job cards using multiple possible selectors
        job_cards = (
            response.css('div.job_seen_beacon') or
            response.css('td.resultContent') or
            response.css('div.cardOutline')
        )

        self.logger.info(f"Found {len(job_cards)} job cards on page {page_num}")

        # Process jobs from this page
        jobs_from_this_page = 0
        for card in job_cards:
            # Exceeded limit
            if self.jobs_scraped >= self.max_results:
                self.logger.info(f"Reached max limit: {self.max_results}")
                break

            job_data = self.parse_job_card(card, response)

            if job_data and self.matches_preferences(job_data):
                # Save job to database immediately with duplicate checking
                try:
                    was_saved = self.save_job_to_database(job_data)
                    if was_saved:
                        self.jobs_scraped += 1
                        jobs_from_this_page += 1
                        self.logger.info(f"Saved job {self.jobs_scraped}: {job_data.get('title')} at {job_data.get('company_name')} (from page {page_num})")
                        yield job_data # not currently used, maybe for future features?
                    else:
                        self.logger.info(f"Duplicate skipped: {job_data.get('title')} at {job_data.get('company_name')} (from page {page_num})")
                except Exception as e:
                    self.logger.error(f"Failed to save job to database: {e}")
                    # Continue processing even if one job fails to save

        self.logger.info(f"Page {page_num} completed: {jobs_from_this_page} jobs matched from {len(job_cards)} total")

        # Publish page completion update with current job count
        try:
            page_update = {
                'status': 'running',
                'jobs_found': self.jobs_scraped,
                'error_message': None,
                'page_completed': page_num,
                'jobs_from_page': jobs_from_this_page
            }
            publish_update(page_update)
            self.logger.info(f"Published page {page_num} update: {self.jobs_scraped} total jobs so far")
        except Exception as e:
            self.logger.error(f"Failed to publish page update: {e}")

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
                card.css('a[data-testid="company-name"]::text').get() or
                card.css('span.companyName a::text').get() or
                card.css('span[data-testid="company-name"]::text').get() or
                card.css('span.companyName::text').get()
            )
            
            # Location
            location = (
                card.css('div[data-testid="text-location"]::text').get() or
                card.css('div.companyLocation::text').get()
            )
            
            # Extract metadata from multiple possible locations
            salary = None
            job_type = None
            benefits_list = []

            # Try multiple metadata selectors
            metadata_selectors = [
                'ul.heading6.tapItem-gutter.metadataContainer li',
                'ul[data-testid="job-details"] li',
                'div[data-testid="job-attribute-group"] div',
                'div.metadata div',
                'ul.heading6 li'
            ]

            for selector in metadata_selectors:
                metadata_items = card.css(selector)
                if metadata_items:
                    break

            for item in metadata_items:
                # Try multiple ways to get text content - updated for current Indeed structure
                metadata_text = (
                    item.css('div[class*="mosaic-provider-jobcards-"]::text').get() or  # Current structure
                    item.css('div::text').get() or
                    item.css('span::text').get() or
                    item.css('::text').get()
                )

                if metadata_text:
                    metadata_text = metadata_text.strip()

                    # Check for salary (contains $ and year/hour)
                    if '$' in metadata_text and ('year' in metadata_text or 'hour' in metadata_text):
                        salary = metadata_text
                    # Check for job type - expand patterns
                    elif any(jt in metadata_text for jt in ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Co-op', 'Permanent', 'Casual']):
                        job_type = metadata_text
                    # Everything else goes to benefits
                    else:
                        benefits_list.append(metadata_text)

            # Combine all benefits into a single string
            benefits = ', '.join(benefits_list) if benefits_list else None

            # Fallback selectors if not found in metadata
            if not salary:
                salary = (
                    card.css('div.salary-snippet-container::text').get() or
                    card.css('span.salary::text').get() or
                    card.css('div[data-testid="salary-text"]::text').get() or
                    card.css('div.salaryText::text').get()
                )

            if not job_type:
                job_type = (
                    card.css('div[data-testid="attribute_snippet_testid"]::text').get() or
                    card.css('span.attribute_snippet::text').get() or
                    card.css('div[data-testid="job-type"]::text').get() or
                    card.css('span.jobtype::text').get()
                )
            
            # Description snippet
            description = card.css('div.job-snippet::text').get()
            
            # Build job URL
            if job_id:
                job_url = f"https://{self.base_domain}/viewjob?jk={job_id}"
            else:
                job_link = card.css('h2.jobTitle a::attr(href)').get()
                if job_link:
                    if job_link.startswith('http'):
                        job_url = job_link
                    elif job_link.startswith('/'):
                        job_url = f"https://{self.base_domain}{job_link}"
                    else:
                        job_url = f"https://{self.base_domain}/{job_link}"
                else:
                    job_url = response.url
            
            # Validate required fields
            if not job_id or not title or not company:
                self.logger.debug(f"Skipping incomplete job: id={job_id}, title={title}, company={company}")
                return None
            
            # Create JobItem matching Pydantic Job schema
            job = JobItem()
            job['external_id'] = job_id.strip()  # Scraper metadata
            job['title'] = title.strip()
            job['company_name'] = company.strip()
            job['location'] = location.strip() if location else ''
            job['job_type'] = job_type.strip() if job_type else ''
            job['salary'] = salary.strip() if salary else None
            job['url'] = job_url
            job['description'] = description.strip() if description else ''
            job['benefits'] = benefits
            
            self.logger.info(f"Scraped job {self.jobs_scraped + 1}: {title} at {company}")
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")
            return None

    def matches_preferences(self, job_data):
        """Filter jobs based on user preferences using OR logic"""

        job_title = job_data.get('title').lower()
        job_company = job_data.get('company_name').lower()
        job_location = (job_data.get('location') or '').lower()
        job_type = (job_data.get('job_type') or '').lower()
        job_description = (job_data.get('description') or '').lower()
        job_salary = (job_data.get('salary') or '').lower()
        job_benefits = (job_data.get('benefits') or '').lower()

        # Debug logging
        self.logger.info(f"=== PREFERENCE CHECK ===")
        
        # Check if job matches ANY of the title preferences (case-insensitive substring)
        if self.preferred_titles:
            title_match = any(pref_title.lower().strip() in job_title.lower().strip()
                            for pref_title in self.preferred_titles if pref_title.strip())
            if not title_match:
                self.logger.info(f"❌ FILTERED OUT: No title match. Prefer: {self.preferred_titles}, actual: {job_title}")
                return False
            
        # Check if job matches ANY of the location preferences (case-insensitive substring)
        if self.preferred_locations:
            location_match = any(pref_loc.lower().strip() in job_location.lower().strip()
                               for pref_loc in self.preferred_locations if pref_loc.strip())
            if not location_match:
                self.logger.info(f"❌ FILTERED OUT: No location match. Prefer: {self.preferred_locations}, actual: {job_location}")
                return False

        # Check if job matches ANY of the company preferences (case-insensitive substring)
        if self.preferred_company_name:
            title_match = any(pref_company.lower().strip() in job_company.lower().strip()
                            for pref_company in self.preferred_company_name if pref_company.strip())
            if not title_match:
                self.logger.info(f"❌ FILTERED OUT: No company match. Prefer: {self.preferred_company_name}, actual: {job_company}")
                return False
            
        # Check if job matches ANY of the job type preferences (case-insensitive substring)
        if self.preferred_job_types:
            job_type_match = any(pref_type.lower().strip() in job_type.lower().strip()
                               for pref_type in self.preferred_job_types if pref_type.strip())
            if not job_type_match:
                self.logger.info(f"❌ FILTERED OUT: No job type match. Prefer: {self.preferred_job_types}, actual: {job_type}")
                return False

        # Check if job matches ANY of the description keywords (case-insensitive substring)
        if self.preferred_descriptions:
            desc_match = any(keyword.lower().strip() in job_description.lower().strip() or
                           keyword.lower().strip() in job_title.lower().strip()
                           for keyword in self.preferred_descriptions if keyword.strip())
            if not desc_match:
                self.logger.debug(f"❌ FILTERED OUT: No description match. Prefer: {self.preferred_descriptions}, actual: {job_description}")
                return False

        # Check if job matches ANY of the salary preferences (case-insensitive substring)
        if self.preferred_salaries:
            salary_match = any(pref_salary.lower().strip() in job_salary.lower().strip()
                             for pref_salary in self.preferred_salaries if pref_salary.strip())
            if not salary_match:
                self.logger.debug(f"❌ FILTERED OUT: No salary match. Prefer: {self.preferred_salaries}, actual: {job_salary}")
                return False

        # Check if job matches ANY of the benefits preferences (case-insensitive substring)
        if self.preferred_benefits:
            benefits_match = any(pref_benefit.lower().strip() in job_benefits.lower().strip()
                               for pref_benefit in self.preferred_benefits if pref_benefit.strip())
            if not benefits_match:
                self.logger.debug(f"❌ FILTERED OUT: No benefits matchPrefer: {self.preferred_benefits}, actual: {job_benefits}")
                return False

        self.logger.info(f"✅ PASSED ALL FILTERS - Job accepted!")
        return True

    def save_job_to_database(self, job_data):
        """Save job to database using environment variables (for subprocess compatibility)"""
        try:
            from supabase import create_client
            from datetime import datetime

            # Get database settings from environment variables
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            user_id = os.environ.get('SCRAPER_USER_ID')

            if not all([supabase_url, supabase_key, user_id]):
                missing = []
                if not supabase_url: missing.append('SUPABASE_URL')
                if not supabase_key: missing.append('SUPABASE_KEY')
                if not user_id: missing.append('SCRAPER_USER_ID')
                raise ValueError(f"Missing environment variables: {missing}")

            # Create Supabase client
            supabase = create_client(supabase_url, supabase_key)

            # Check for duplicate jobs based on title, company, and location
            title = (job_data.get('title') or '').strip()
            company = (job_data.get('company_name') or '').strip()
            location = (job_data.get('location') or '').strip()

            # Query for existing jobs with same title, company, and location for this user
            existing_jobs = supabase.table('jobs').select('id').eq('user_id', user_id).eq('title', title).eq('company_name', company).eq('location', location).execute()

            if existing_jobs.data:
                self.logger.debug(f"Duplicate job found: {title} at {company} in {location} - skipping")
                return False  # Indicate duplicate was found and skipped

            # Prepare job data for database
            job_record = {
                'user_id': user_id,
                'title': title,
                'company_name': company,
                'location': location,
                'job_type': job_data.get('job_type'),
                'salary': (job_data.get('salary') or ''),
                'url': (job_data.get('url') or ''),
                'description': (job_data.get('description') or ''),
                'benefits': (job_data.get('benefits') or '')
            }

            # Insert into database
            jobs_result = supabase.table('jobs').insert(job_record).execute()
            
            # Update user stats
            current = supabase.table('user_statistics').select('*').eq('user_id', user_id).execute()
            if current.data:
                stats = current.data[0]
            stats['total_jobs'] += 1
            stats['current_jobs'] += 1
            stats['latest_scrape'] = datetime.now().astimezone().isoformat()
            stats_result = supabase.table('user_statistics').update(stats).eq('user_id', user_id).execute()
            
            self.logger.debug(f"Database insert result: {jobs_result}")
            self.logger.debug(f"Database update result: {stats_result}")
            return True  # Indicate successful save

        except Exception as e:
            self.logger.error(f"Database save error: {e}")
            raise

    def handle_error(self, failure):
        """Handle request errors - gracefully handle timeouts"""
        self.logger.error(f"=== REQUEST FAILED ===")
        self.logger.error(f"URL: {failure.request.url}")
        self.logger.error(f"Error type: {type(failure.value)}")
        self.logger.error(f"Error details: {failure.value}")

        # Check if this is a timeout error
        is_timeout = (
            'TimeoutError' in str(type(failure.value)) or
            'timeout' in str(failure.value).lower() or
            'Timeout' in str(failure.value)
        )

        if is_timeout:
            self.logger.info(f"=== TIMEOUT DETECTED - PRESERVING {self.jobs_scraped} JOBS ===")
            self.logger.info(f"Jobs found so far: {self.jobs_scraped}")
            self.logger.info(f"Pages processed: {self.pages_visited}")

            # Don't stop the spider - let it finish naturally with jobs found so far
            # The spider will complete and return the jobs it has collected
            return
        else:
            # For non-timeout errors, log and continue
            self.logger.error(f"Non-timeout error occurred: {failure.value}")
            self.logger.info(f"Continuing with {self.jobs_scraped} jobs found so far")
            return
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info(f"=== Spider Closed ===")
        self.logger.info(f"Reason: {reason}")
        self.logger.info(f"Total jobs scraped: {self.jobs_scraped}")
        self.logger.info(f"Pages processed: {self.pages_visited}")

        # Update total_scrapes once per scraping session
        if not self.scrape_session_counted:
            try:
                from supabase import create_client
                import os

                # Get database settings from environment variables
                supabase_url = os.environ.get('SUPABASE_URL')
                supabase_key = os.environ.get('SUPABASE_KEY')
                user_id = os.environ.get('SCRAPER_USER_ID')

                if all([supabase_url, supabase_key, user_id]):
                    # Create Supabase client
                    supabase = create_client(supabase_url, supabase_key)

                    # Update total_scrapes by 1 for this scraping session
                    current = supabase.table('user_statistics').select('*').eq('user_id', user_id).execute()
                    if current.data:
                        stats = current.data[0]
                        stats['total_scrapes'] += 1
                        supabase.table('user_statistics').update(stats).eq('user_id', user_id).execute()
                        self.logger.info(f"Incremented total_scrapes to {stats['total_scrapes']}")
                        self.scrape_session_counted = True
                else:
                    self.logger.warning("Could not update total_scrapes - missing environment variables")
            except Exception as e:
                self.logger.error(f"Failed to update total_scrapes: {e}")

        # Publish final completion update with accurate job count
        try:
            completion_update = {
                'status': 'completed',
                'jobs_found': self.jobs_scraped,
                'error_message': None,
                'spider_finished': True  # Signal that spider is completely done
            }
            publish_update(completion_update)
            self.logger.info(f"Published final completion update: {self.jobs_scraped} jobs found")
        except Exception as e:
            self.logger.error(f"Failed to publish completion update: {e}")

        if self.jobs_scraped > 0:
            self.logger.info(f"SUCCESS: Found {self.jobs_scraped} jobs from {self.pages_visited} page(s)")
        else:
            self.logger.warning(f"NO JOBS FOUND after {self.pages_visited} page(s)")

        if reason == 'finished' and self.jobs_scraped < self.max_results:
            self.logger.info(f"Note: Stopped before reaching max results ({self.max_results}) - this may be due to timeouts or filtering")