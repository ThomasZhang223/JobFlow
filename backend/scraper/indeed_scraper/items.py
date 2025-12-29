# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobItem(scrapy.Item):
    """Data structure for a scraped job listing"""
    external_id = scrapy.Field()
    title = scrapy.Field()
    company_name = scrapy.Field()
    location = scrapy.Field()
    salary_text = scrapy.Field()
    job_type = scrapy.Field()
    description = scrapy.Field()
    application_url = scrapy.Field()
    posted_date = scrapy.Field()
    search_query = scrapy.Field()
    search_location = scrapy.Field()
    scraped_at = scrapy.Field()