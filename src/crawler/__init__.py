"""
Generic Web Crawler Module
==========================

Crawl and extract content from any website.
Not tied to any specific platform.

Usage:
    from src.crawler import UniversalCrawler
    
    crawler = UniversalCrawler(config)
    crawler.crawl_urls(['https://example.com/docs'])
"""

from .universal_crawler import UniversalCrawler, CrawlConfig
from .url_discovery import URLDiscovery

__all__ = ['UniversalCrawler', 'CrawlConfig', 'URLDiscovery']
