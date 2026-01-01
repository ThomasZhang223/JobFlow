import scrapy


class JobItem(scrapy.Item):
    """
    Scrapy item for job data that maps to the database Job schema.
    Includes both database fields and scraper-specific metadata.
    """

    # Database Job schema fields (from backend/app/schemas/database_tables.py)
    title = scrapy.Field()
    company_name = scrapy.Field()
    location = scrapy.Field()
    job_type = scrapy.Field()
    description = scrapy.Field()  # Job description snippet
    salary = scrapy.Field()  # Maps to salardy_text from spider
    url = scrapy.Field()  # Maps to application_url from spider
    posted_date = scrapy.Field()

    # Scraper-specific metadata fields
    external_id = scrapy.Field()  # Indeed job ID
    search_query = scrapy.Field()  # Original search query used
    search_location = scrapy.Field()  # Original search location used
    scraped_at = scrapy.Field()  # Timestamp when scraped