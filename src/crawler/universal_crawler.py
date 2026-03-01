"""
Universal Web Crawler
=====================

Generic crawler that works with any website.
Configurable delay, retries, and content extraction.
"""

import time
import requests
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CrawlConfig:
    """Configuration for crawling"""
    delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    output_dir: str = "./data/raw"
    user_agent: str = "RAG-Data-Pipeline/1.0"


class UniversalCrawler:
    """
    Generic web crawler for any documentation site.
    
    Example:
        config = CrawlConfig(delay=2.0, output_dir="./my_docs")
        crawler = UniversalCrawler(config)
        
        # Crawl single URL
        result = crawler.crawl_url("https://example.com/docs")
        
        # Crawl multiple URLs
        crawler.crawl_urls(["https://example.com/page1", "https://example.com/page2"])
    """
    
    def __init__(self, config: Optional[CrawlConfig] = None):
        self.config = config or CrawlConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent
        })
        self.output_path = Path(self.config.output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    def crawl_url(self, url: str, extractor: Optional[Callable] = None) -> dict:
        """
        Crawl a single URL.
        
        Args:
            url: URL to crawl
            extractor: Optional custom content extractor function
            
        Returns:
            dict with url, content, success status
        """
        logger.info(f"Crawling: {url}")
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url, 
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                
                # Use custom extractor or default
                if extractor:
                    content = extractor(response.text, url)
                else:
                    content = self._default_extract(response.text, url)
                
                # Save to file
                filename = self._url_to_filename(url)
                filepath = self.output_path / filename
                filepath.write_text(content, encoding='utf-8')
                
                logger.info(f"✓ Saved: {filepath}")
                
                # Respect delay
                time.sleep(self.config.delay)
                
                return {
                    'url': url,
                    'success': True,
                    'filepath': str(filepath),
                    'content_length': len(content)
                }
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"✗ Failed after {self.config.max_retries} attempts: {url}")
                    return {
                        'url': url,
                        'success': False,
                        'error': str(e)
                    }
        
        return {'url': url, 'success': False, 'error': 'Max retries exceeded'}
    
    def crawl_urls(self, urls: List[str], extractor: Optional[Callable] = None) -> List[dict]:
        """
        Crawl multiple URLs.
        
        Args:
            urls: List of URLs to crawl
            extractor: Optional custom content extractor
            
        Returns:
            List of results
        """
        results = []
        for url in urls:
            result = self.crawl_url(url, extractor)
            results.append(result)
        
        # Summary
        success_count = sum(1 for r in results if r.get('success'))
        logger.info(f"\nCrawl complete: {success_count}/{len(urls)} successful")
        
        return results
    
    def _default_extract(self, html: str, url: str) -> str:
        """Default extraction - just save raw HTML"""
        return html
    
    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        # Remove protocol
        name = url.replace('https://', '').replace('http://', '')
        # Replace special chars
        name = name.replace('/', '_').replace('?', '_').replace('&', '_')
        # Limit length
        if len(name) > 200:
            name = name[:200]
        return name + '.html'
