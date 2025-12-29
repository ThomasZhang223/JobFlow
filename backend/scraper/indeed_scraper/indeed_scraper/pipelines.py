# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from datetime import datetime
import re


class DataCleaningPipeline:
    """Cleans and normalizes scraped data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean text fields
        text_fields = ['title', 'company_name', 'location', 'salary_text']
        for field in text_fields:
            if adapter.get(field):
                value = adapter[field].strip()
                value = re.sub(r'\s+', ' ', value)
                adapter[field] = value
        
        # Ensure URL is absolute
        if adapter.get('application_url'):
            url = adapter['application_url']
            if url.startswith('/'):
                adapter['application_url'] = f'https://www.indeed.com{url}'
        
        return item