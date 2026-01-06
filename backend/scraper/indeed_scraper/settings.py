# Scrapy settings for indeed_scraper project

BOT_NAME = 'indeed_scraper'

SPIDER_MODULES = ['indeed_scraper.spiders']
NEWSPIDER_MODULE = 'indeed_scraper.spiders'

# Obey robots.txt (set to False for now)
ROBOTSTXT_OBEY = False

# Configure delays
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# Cookies - ENABLE for Cloudflare challenges
COOKIES_ENABLED = True

# Headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_TYPE = "chromium"

'''
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'indeed_scraper.middlewares.ProxyMiddleware': 750,
}

PROXY_LIST = [
    'http://uyddgisl:xp94bd2fpxkp@142.111.48.253:7030',
    'http://uyddgisl:xp94bd2fpxkp@23.95.150.145:6114',
    'http://uyddgisl:xp94bd2fpxkp@198.23.239.134:6540',
    'http://uyddgisl:xp94bd2fpxkp@107.172.163.27:6543',
    'http://uyddgisl:xp94bd2fpxkp@198.105.121.200:6462',
    'http://uyddgisl:xp94bd2fpxkp@64.137.96.74:6641',
    'http://uyddgisl:xp94bd2fpxkp@84.247.60.125:6095',
    'http://uyddgisl:xp94bd2fpxkp@216.10.27.159:6837',
    'http://uyddgisl:xp94bd2fpxkp@23.26.71.145:5628',
    'http://uyddgisl:xp94bd2fpxkp@23.27.208.120:5830',
]

ROTATING_PROXY_LIST = PROXY_LIST
'''

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 403]

# Pipelines
ITEM_PIPELINES = {
    'indeed_scraper.pipelines.DataCleaningPipeline': 100,
}

# Logging
LOG_LEVEL = 'DEBUG'
FEED_EXPORT_ENCODING = 'utf-8'
