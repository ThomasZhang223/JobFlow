"""
Simple curl_cffi middleware for Scrapy
Bypasses Cloudflare TLS fingerprinting while keeping Scrapy's parallel scheduling
"""

from scrapy.http import HtmlResponse
from curl_cffi import requests


class CurlCffiMiddleware:
    """Uses curl_cffi to make requests with Chrome's TLS fingerprint"""

    def __init__(self):
        self.session = requests.Session(impersonate="chrome120")

    def process_request(self, request, spider):
        """Intercept request and use curl_cffi instead"""

        try:
            response = self.session.get(
                request.url,
                headers=dict(request.headers.to_unicode_dict()),
                timeout=30,
                allow_redirects=True
            )

            # Remove Content-Encoding header to prevent Scrapy from trying to decompress
            headers_dict = dict(response.headers)
            headers_dict.pop('Content-Encoding', None)
            headers_dict.pop('content-encoding', None)

            return HtmlResponse(
                url=response.url,
                status=response.status_code,
                headers=headers_dict,
                body=response.text.encode('utf-8'),
                encoding='utf-8',
                request=request
            )

        except Exception as e:
            spider.logger.error(f"curl_cffi request failed: {e}")
            raise
