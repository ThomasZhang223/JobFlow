import scrapy
import math
import os
import sys
from datetime import datetime
from urllib.parse import urlencode
import json

# Import anti-bot measures
from indeed_scraper.user_agents import get_random_user_agent
from indeed_scraper.proxies import get_proxy

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

        """
        # Read Redis settings from environment variables
        upstash_redis_rest_url = os.environ.get('UPSTASH_REDIS_REST_URL')
        upstash_redis_rest_token = os.environ.get('UPSTASH_REDIS_REST_TOKEN')
        upstash_redis_port = os.environ.get('UPSTASH_REDIS_PORT')
        scrape_update_channel = os.environ.get('SCRAPE_UPDATE_CHANNEL')

        if not upstash_redis_rest_url or not upstash_redis_rest_token or not scrape_update_channel:
            print(f'No Redis connection available')
            return

        # Build TCP connection URL (same as backend)
        connection_url = f"rediss://:{upstash_redis_rest_token}@{upstash_redis_rest_url[8:]}:{upstash_redis_port}?ssl_cert_reqs=required"
        """
        # Redis URL from environment (Docker) or fallback to localhost (local dev)
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        scrape_update_channel = os.environ.get('SCRAPE_UPDATE_CHANNEL', 'scrape_update')
        
        # Create Redis client with TCP connection
        #r = redis.from_url(connection_url)
        r = redis.from_url(redis_url)
        
        message_json = json.dumps(message)

        # Publish via TCP (so backend subscriber receives it)
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
        # PARALLEL LOADING: Multiple pages at once
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 4,  
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
        'RANDOMIZE_DOWNLOAD_DELAY': False,
        'RETRY_TIMES': 3,

        # AUTOTHROTTLE: Let Scrapy adjust speed based on server response
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,  # Start slow
        'AUTOTHROTTLE_MAX_DELAY': 15,  # Max delay if server struggling
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,  # Target 1 concurrent (sequential)
        'AUTOTHROTTLE_DEBUG': False,
        'LOG_LEVEL': 'INFO',

        # Anti-bot measures
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,  # Required for Cloudflare challenges
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
    
    def __init__(self, user_id=None, preferences=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Store user_id for Redis publishing
        if not user_id:
            raise ValueError("user_id parameter is required")
        self.user_id = user_id

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

    def make_request(self, url, callback, **kwargs):
        """Create a Playwright request with rotating proxy and user agent"""
        headers = {}
        
        user_agent = get_random_user_agent()
        headers['User-Agent'] = user_agent
        
        self.logger.info(f"Using user agent: {user_agent[:60]}...")

        request = scrapy.Request(
            url=url,
            callback=callback,
            headers=headers,
            **kwargs
        )
        
        proxy = get_proxy()
        request.meta['playwright_context_kwargs'] = {
            'proxy': {
                'server': proxy[0],
                'username': proxy[1],
                'password': proxy[2]
            }
        }
        
        self.logger.info(f"Using user agent: {user_agent[:60]}...")
        self.logger.info(f"Using proxy: {proxy[0]}...")
        
        return request

    def start_requests(self):
        """Load multiple pages in parallel"""
        # Calculate pages needed (assume ~13 jobs per page)
        estimated_pages = min(max(1, math.ceil(self.max_results/13)), self.max_pages)

        self.logger.info(f"=== PARALLEL LOADING {estimated_pages} PAGES ===")

        # Yield all page requests at once
        for page_num in range(estimated_pages):
            page_url = self.get_indeed_search_url(page_num)
            
            # Stagger the requests slightly to avoid simultaneous hits
            wait_time = 2000 + (page_num * 1000)  # 2s, 3s, 4s, etc.  
                  
            yield self.make_request(
                url=page_url,
                callback=self.parse_search_results,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_goto_kwargs': {'wait_until': 'domcontentloaded', 'timeout': 60000},
                    'playwright_page_methods': [
                        {'method': 'wait_for_timeout', 'args': [wait_time]}
                    ],
                    'page_number': page_num + 1,
                    },
                errback=self.handle_error,
                dont_filter=True
            )

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
    
    def parse_search_results(self, response):
        """Parse search results from parallel pages"""
        page_num = response.meta.get('page_number')
        self.pages_visited += 1

        self.logger.info(f"Parsing page {page_num}: {response.url} (status: {response.status})")

        # Check for bot detection or HTTP errors
        if 'secure.indeed.com/auth' in response.url or response.status >= 400:
            error_msg = f'HTTP {response.status} error on page {page_num}' if response.status >= 400 else 'Bot detection redirect'
            try:
                failure_update = {
                    'user_id': self.user_id,
                    'status': 'failed',
                    'jobs_found': self.jobs_scraped,
                    'error_message': error_msg,
                    'spider_finished': True
                }
                publish_update(failure_update)
            except Exception as e:
                self.logger.error(f"Failed to publish failure update: {e}")
            self.logger.error(error_msg)
            return

        # Find job cards
        job_cards = (
            response.css('div.job_seen_beacon') or
            response.css('td.resultContent') or
            response.css('div.cardOutline')
        )

        self.logger.info(f"Found {len(job_cards)} job cards on page {page_num}")

        # Process jobs
        for card in job_cards:
            if self.jobs_scraped >= self.max_results:
                break

            job_data = self.parse_job_card(card)

            if job_data and self.matches_preferences(job_data):
                try:
                    was_saved = self.save_job_to_database(job_data)
                    if was_saved:
                        self.jobs_scraped += 1
                        self.logger.info(f"Saved job {self.jobs_scraped}: {job_data.get('title')} at {job_data.get('company_name')} (page {page_num})")
                        yield job_data
                    else:
                        self.logger.info(f"Duplicate skipped: {job_data.get('title')} at {job_data.get('company_name')}")
                except Exception as e:
                    self.logger.error(f"Failed to save job: {e}")

        # Publish page update
        try:
            page_update = {
                'user_id': self.user_id,
                'status': 'running',
                'jobs_found': self.jobs_scraped,
                'page_completed': page_num,
            }
            publish_update(page_update)
        except Exception as e:
            self.logger.error(f"Failed to publish update: {e}")

    def parse_job_card(self, card):
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
                    job_url = ''
                
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
            job['benefits'] = benefits
            job['description'] = ''  # Description fetching disabled to reduce requests by 50%
            
            self.logger.info(f"Scraped job {self.jobs_scraped + 1}: {title} at {company}")
            return job

        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")

    """
    DISABLED DESCRIPTION FOR NOW TO AVOID IP BAN
    
    def parse_description(self, response):         
        job = response.meta['job_data']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
        try:                                                                                                                                                                                                 
            selectors = [                                                                                                                                                                                    
            'div[id="jobDescriptionText"]',                                                                                                                                                              
            'div[class*="jobsearch-JobComponent-description"]',                                                                                                                                          
            'div.jobsearch-jobDescriptionText',                                                                                                                                                          
            ]                                                                                                                                                                                                
                                                                                                                                                                                                            
            job_div = None                                                                                                                                                                                   
            for selector in selectors:                                                                                                                                                                       
                job_div = response.css(selector)                                                                                                                                                             
                if job_div:                                                                                                                                                                                  
                    break                                                                                                                                                                                    
                                                                                                                                                                                                             
            if not job_div:                                                                                                                                                                                  
                self.logger.warning(f"Job description container not found for {job.get('title')}")                                                                                                           
                job['description'] = ''                                                                                                                                                                      
            else:                                                                                                                                                                                            
                # Block-level elements that should have newlines after them                                                                                                                                  
                block_elements = ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'br']                                                                                                    
                                                                                                                                                                                                             
                formatted_text = []                                                                                                                                                                          
                                                                                                                                                                                                            
                # Get all elements in order                                                                                                                                                                  
                for element in job_div.css('*'):                                                                                                                                                             
                    element_tag = element.root.tag                                                                                                                                                           
                                                                                                                                                                                                             
                   # Extract text from this element (not descendants)                                                                                                                                       
                    text = ''.join(element.xpath('./text()').getall()).strip()                                                                                                                               
                                                                                                                                                                                                             
                    if text and text not in ['...', '…']:                                                                                                                                                    
                        # Add extra spacing for headers                                                                                                                                                      
                        if element_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:                                                                                                                              
                            formatted_text.append(f'\n{text}\n')                                                                                                                                             
                        # Regular block elements                                                                                                                                                             
                        elif element_tag in block_elements:                                                                                                                                                  
                            formatted_text.append(text)                                                                                                                                                      
                            # Add newline after block elements (unless it's a br)                                                                                                                            
                            if element_tag != 'br':                                                                                                                                                          
                                 formatted_text.append('\n')                                                                                                                                                  
                        else:                                                                                                                                                                                
                            # Inline elements - just add the text with space                                                                                                                                 
                            formatted_text.append(text + ' ')                                                                                                                                                
                                                                                                                                                                                                             
                full_text = ''.join(formatted_text)                                                                                                                                                          
                                                                                                                                                                                                             
                # Clean up excessive newlines (max 2 consecutive)                                                                                                                                            
                import re                                                                                                                                                                                    
                full_text = re.sub(r'\n{3,}', '\n\n', full_text)                                                                                                                                             
                full_text = re.sub(r' +', ' ', full_text)  # Multiple spaces to single                                                                                                                       
                full_text = full_text.strip()                                                                                                                                                                
                                                                                                                                                                                                             
                job['description'] = full_text                                                                                                                                                               
                self.logger.debug(f'Fetched description for: {job.get("title")} ({len(full_text)} chars)')                                                                                                   
                                                                                                                                                                                                             
            # Now check if job matches preferences (including description)                                                                                                                                   
            if self.matches_preferences(job):                                                                                                                                                                
                # Save job to database with duplicate checking                                                                                                                                               
                try:                                                                                                                                                                                         
                    was_saved = self.save_job_to_database(job)                                                                                                                                               
                    if was_saved:                                                                                                                                                                            
                        self.jobs_scraped += 1                                                                                                                                                               
                        self.logger.info(f"✓ Saved job {self.jobs_scraped}: {job.get('title')} at {job.get('company_name')}")                                                                                
                    else:                                                                                                                                                                                    
                        self.logger.info(f"Duplicate skipped: {job.get('title')} at {job.get('company_name')}")                                                                                              
                except Exception as e:                                                                                                                                                                       
                    self.logger.error(f"Failed to save job to database: {e}")                                                                                                                                
            else:                                                                                                                                                                                            
                self.logger.info(f"❌ Filtered out: {job.get('title')} (didn't match preferences)")                                                                                                           
                                                                                                                                                                                                             
        except Exception as e:                                                                                                                                                                               
            self.logger.error(f"Error parsing description: {e}")                                                                                                                                             
    """                                                       

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
            
        # Check if job matches ANY of the job type preferences (case-insensitive substring) --- checks both title and job type
        if self.preferred_job_types:
            job_type_match = any(pref_type.lower().strip() in job_type.lower().strip() or
                                pref_type.lower().strip() in job_title.lower().strip()
                               for pref_type in self.preferred_job_types if pref_type.strip())
            if not job_type_match:
                self.logger.info(f"❌ FILTERED OUT: No job type match. Prefer: {self.preferred_job_types}, actual: {job_type}")
                return False

        # Check if job matches ANY of the description keywords (case-insensitive substring) --- checks both title and description
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
            # For non-timeout errors, publish failure update
            self.logger.error(f"Non-timeout error occurred: {failure.value}")
            self.logger.info(f"Continuing with {self.jobs_scraped} jobs found so far")

            # Publish error update
            try:
                error_update = {
                    'user_id': self.user_id,
                    'status': 'failed',
                    'jobs_found': self.jobs_scraped,
                    'error_message': str(failure.value),
                    'spider_finished': True
                }
                publish_update(error_update)
            except Exception as e:
                self.logger.error(f"Failed to publish error update: {e}")

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
                'user_id': self.user_id,
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