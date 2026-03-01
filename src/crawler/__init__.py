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

from .universal_crawler import UniversalCrawler
from .url_discovery import URLDiscovery
from .content_extractor import ContentExtractor

__all__ = ['UniversalCrawler', 'URLDiscovery', 'ContentExtractor']
