"""
Crawler Engine Module
=====================

Main crawling engine with support for both requests and Playwright.
"""

import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from src.config_loader import ConfigLoader
from src.queue_manager import QueueManager
from src.content_extractor import ContentExtractor
from src.url_discovery import URLDiscovery


logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result of crawling a single URL."""
    url: str
    success: bool
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    crawl_time: float = 0.0


class CrawlerEngine:
    """Main crawling engine for Odoo documentation."""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        Initialize crawler engine.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config or ConfigLoader()
        self.queue_manager = QueueManager(config)
        self.content_extractor = ContentExtractor(config)
        self.url_discovery = URLDiscovery(config)
        
        # Crawler settings
        self.delay = self.config.get_delay()
        self.timeout = self.config.get('crawler.timeout', 30)
        self.max_retries = self.config.get('crawler.max_retries', 3)
        self.use_playwright = self.config.get('crawler.use_playwright', True)
        self.playwright_patterns = self.config.get('crawler.playwright_patterns', [])
        
        # Storage settings
        self.raw_docs_path = Path(self.config.get_raw_docs_path())
        self.organize_by_category = self.config.get('storage.organize_by_category', True)
        
        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.get_user_agent()
        })
        
        # Playwright instance
        self._playwright = None
        self._browser = None
    
    async def _init_playwright(self) -> Optional[Browser]:
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE or not self.use_playwright:
            return None
        
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            logger.info("Playwright initialized successfully")
            return self._browser
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            self.use_playwright = False
            return None
    
    async def _close_playwright(self) -> None:
        """Close Playwright browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    def _should_use_playwright(self, url: str) -> bool:
        """Check if URL should use Playwright."""
        if not self.use_playwright or not PLAYWRIGHT_AVAILABLE:
            return False
        
        import re
        for pattern in self.playwright_patterns:
            if re.match(pattern, url):
                return True
        
        return False
    
    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """
        Fetch page using Playwright.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None
        """
        if not self._browser:
            return None
        
        try:
            context = await self._browser.new_context(
                user_agent=self.config.get_user_agent()
            )
            page = await context.new_page()
            
            # Navigate and wait for content
            await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
            
            # Wait for main content to load
            selectors = self.config.get_selectors()
            main_selector = selectors.get('main_content', 'main').split(',')[0]
            
            try:
                await page.wait_for_selector(main_selector, timeout=5000)
            except:
                pass  # Continue even if selector not found
            
            # Get HTML content
            html = await page.content()
            
            await context.close()
            
            return html
            
        except Exception as e:
            logger.error(f"Playwright error fetching {url}: {e}")
            return None
    
    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """
        Fetch page using requests.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None
        """
        try:
            response = self.session.get(
                url, 
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Request error fetching {url}: {e}")
            return None
    
    async def fetch(self, url: str) -> Optional[str]:
        """
        Fetch page content (uses Playwright if needed).
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None
        """
        if self._should_use_playwright(url):
            logger.debug(f"Using Playwright for {url}")
            return await self._fetch_with_playwright(url)
        else:
            return self._fetch_with_requests(url)
    
    async def crawl_url(self, url: str, retry_count: int = 0) -> CrawlResult:
        """
        Crawl a single URL.
        
        Args:
            url: URL to crawl
            retry_count: Current retry attempt
            
        Returns:
            CrawlResult object
        """
        start_time = time.time()
        
        # Check if already crawled
        if self.queue_manager.is_crawled(url):
            self.stats['skipped'] += 1
            return CrawlResult(
                url=url,
                success=True,
                crawl_time=time.time() - start_time
            )
        
        logger.info(f"Crawling: {url}")
        
        # Fetch content
        html = await self.fetch(url)
        
        if html is None:
            error_msg = "Failed to fetch page"
            
            # Retry if needed
            if retry_count < self.max_retries:
                logger.warning(f"Retrying {url} (attempt {retry_count + 1})")
                await asyncio.sleep(self.delay * (retry_count + 1))
                return await self.crawl_url(url, retry_count + 1)
            
            self.queue_manager.mark_failed(url, error_msg, retry_count)
            self.stats['failed'] += 1
            
            return CrawlResult(
                url=url,
                success=False,
                error=error_msg,
                retry_count=retry_count,
                crawl_time=time.time() - start_time
            )
        
        # Extract content
        content = self.content_extractor.extract_content(html, url)
        
        if content is None:
            error_msg = "Failed to extract content"
            self.queue_manager.mark_failed(url, error_msg, retry_count)
            self.stats['failed'] += 1
            
            return CrawlResult(
                url=url,
                success=False,
                error=error_msg,
                retry_count=retry_count,
                crawl_time=time.time() - start_time
            )
        
        # Save content
        saved = await self._save_content(content, url)
        
        if saved:
            self.queue_manager.mark_crawled(url, content['metadata'])
            self.stats['success'] += 1
        else:
            error_msg = "Failed to save content"
            self.queue_manager.mark_failed(url, error_msg, retry_count)
            self.stats['failed'] += 1
            
            return CrawlResult(
                url=url,
                success=False,
                error=error_msg,
                retry_count=retry_count,
                crawl_time=time.time() - start_time
            )
        
        return CrawlResult(
            url=url,
            success=True,
            content=content,
            crawl_time=time.time() - start_time
        )
    
    async def _save_content(self, content: Dict[str, Any], url: str) -> bool:
        """
        Save extracted content to file.
        
        Args:
            content: Content dictionary
            url: Source URL
            
        Returns:
            True if saved successfully
        """
        try:
            # Determine file path
            category = content['metadata'].get('category', 'unknown')
            
            if self.organize_by_category:
                save_dir = self.raw_docs_path / category
            else:
                save_dir = self.raw_docs_path
            
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename from URL
            filename = self._generate_filename(url)
            filepath = save_dir / f"{filename}.md"
            
            # Save using content extractor
            return self.content_extractor.save_markdown(content, filepath)
            
        except Exception as e:
            logger.error(f"Error saving content for {url}: {e}")
            return False
    
    def _generate_filename(self, url: str) -> str:
        """
        Generate safe filename from URL.
        
        Args:
            url: URL to convert
            
        Returns:
            Safe filename
        """
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Remove documentation version prefix
        path = path.replace('documentation/19.0/', '')
        path = path.replace('documentation/19.0', '')
        
        # Replace special characters
        filename = path.replace('/', '_').replace('\\', '_')
        
        # Remove or replace unsafe characters
        import re
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        # Use index if empty
        if not filename:
            filename = 'index'
        
        return filename
    
    async def run(self, urls: Optional[List[str]] = None, 
                  max_pages: Optional[int] = None,
                  progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run the crawler.
        
        Args:
            urls: List of URLs to crawl (uses queue if None)
            max_pages: Maximum number of pages to crawl
            progress_callback: Optional callback for progress updates
            
        Returns:
            Statistics dictionary
        """
        self.stats['start_time'] = datetime.now()
        
        # Initialize Playwright if needed
        if self.use_playwright:
            await self._init_playwright()
        
        try:
            # Add URLs to queue
            if urls:
                self.queue_manager.add_many_to_queue(urls)
            
            # Get total count
            total_urls = self.queue_manager.get_queue_size()
            if max_pages:
                total_urls = min(total_urls, max_pages)
            
            self.stats['total'] = total_urls
            
            logger.info(f"Starting crawl of {total_urls} pages")
            
            # Create progress bar
            pbar = tqdm(total=total_urls, desc="Crawling")
            
            crawled_count = 0
            
            while crawled_count < total_urls:
                url = self.queue_manager.get_next()
                
                if url is None:
                    break
                
                # Crawl URL
                result = await self.crawl_url(url)
                crawled_count += 1
                
                # Update progress
                pbar.update(1)
                pbar.set_postfix({
                    'success': self.stats['success'],
                    'failed': self.stats['failed']
                })
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(result)
                
                # Rate limiting
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
            
            pbar.close()
            
        finally:
            # Cleanup
            await self._close_playwright()
            self.queue_manager.save_state()
        
        self.stats['end_time'] = datetime.now()
        
        return self.get_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get crawling statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()
        
        # Calculate duration
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            stats['duration_seconds'] = duration.total_seconds()
        
        # Add queue stats
        stats['queue'] = self.queue_manager.get_stats()
        
        return stats
    
    def discover_and_crawl(self, start_urls: Optional[List[str]] = None,
                          max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Discover URLs and crawl them.
        
        Args:
            start_urls: Starting URLs for discovery
            max_pages: Maximum pages to crawl
            
        Returns:
            Statistics dictionary
        """
        # Discover URLs
        logger.info("Discovering URLs...")
        discovered = self.url_discovery.discover_all(
            use_sitemap=True,
            use_sidebar=True
        )
        
        logger.info(f"Discovered {len(discovered)} URLs")
        
        # Filter URLs
        filtered = self.url_discovery.filter_urls(discovered)
        logger.info(f"After filtering: {len(filtered)} URLs")
        
        # Run crawler
        return asyncio.run(self.run(filtered, max_pages))
