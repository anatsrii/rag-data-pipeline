"""
URL Discovery Module
====================

Handles discovery of URLs from sitemaps, sidebars, and page crawling.
"""

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional, Dict
import logging

import requests
from bs4 import BeautifulSoup

from src.config_loader import ConfigLoader


logger = logging.getLogger(__name__)


class URLDiscovery:
    """Discover URLs from Odoo documentation."""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        Initialize URL discovery.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config or ConfigLoader()
        self.base_url = self.config.get_base_url()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.get_user_agent()
        })
        self.discovered_urls: Set[str] = set()
    
    def discover_from_sitemap(self, sitemap_url: Optional[str] = None) -> List[str]:
        """
        Discover URLs from XML sitemap.
        
        Args:
            sitemap_url: URL of the sitemap (uses config default if None)
            
        Returns:
            List of discovered URLs
        """
        if sitemap_url is None:
            sitemaps = self.config.get('odoo.sitemaps', [])
            if not sitemaps:
                logger.warning("No sitemap URLs configured")
                return []
            sitemap_url = sitemaps[0]
        
        urls = []
        try:
            logger.info(f"Fetching sitemap: {sitemap_url}")
            response = self.session.get(sitemap_url, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle sitemap index (multiple sitemaps)
            if 'sitemapindex' in root.tag:
                for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                    nested_sitemap_url = sitemap.text
                    if nested_sitemap_url:
                        urls.extend(self.discover_from_sitemap(nested_sitemap_url))
            else:
                # Regular sitemap with URLs
                for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                    if url_elem.text:
                        urls.append(url_elem.text)
                        self.discovered_urls.add(url_elem.text)
            
            logger.info(f"Discovered {len(urls)} URLs from sitemap")
            
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
        
        return urls
    
    def discover_from_sidebar(self, start_url: Optional[str] = None) -> List[str]:
        """
        Discover URLs by parsing sidebar navigation from main pages.
        
        Args:
            start_url: Starting URL (uses config default if None)
            
        Returns:
            List of discovered URLs
        """
        if start_url is None:
            start_url = self.config.get('odoo.developer_url')
        
        urls = []
        try:
            logger.info(f"Discovering from sidebar: {start_url}")
            response = self.session.get(start_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find sidebar navigation links
            # Odoo docs typically use specific classes for navigation
            sidebar_selectors = [
                '.sidebar',
                '.o_side_nav',
                '.side-nav',
                'nav[role="navigation"]',
                '.toc',
                '.toctree-wrapper'
            ]
            
            for selector in sidebar_selectors:
                sidebar = soup.select_one(selector)
                if sidebar:
                    links = sidebar.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        full_url = urljoin(start_url, href)
                        # Only include URLs from the same domain
                        if self._is_same_domain(full_url):
                            urls.append(full_url)
                            self.discovered_urls.add(full_url)
                    break
            
            logger.info(f"Discovered {len(urls)} URLs from sidebar")
            
        except Exception as e:
            logger.error(f"Error discovering from sidebar {start_url}: {e}")
        
        return urls
    
    def discover_from_page_links(self, url: str, depth: int = 1) -> List[str]:
        """
        Discover URLs by following links from a page.
        
        Args:
            url: Starting URL
            depth: How many levels to follow links (default: 1)
            
        Returns:
            List of discovered URLs
        """
        if depth <= 0:
            return []
        
        urls = []
        try:
            logger.info(f"Discovering links from page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find all links in main content area
            main_content = soup.select_one(self.config.get('odoo.selectors.main_content', 'main'))
            if main_content:
                links = main_content.find_all('a', href=True)
            else:
                links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                # Skip anchors and external links
                if href.startswith('#') or href.startswith('mailto:'):
                    continue
                
                full_url = urljoin(url, href)
                
                # Only include URLs from the same domain and documentation path
                if self._is_valid_doc_url(full_url):
                    urls.append(full_url)
                    self.discovered_urls.add(full_url)
                    
                    # Recursively discover if depth > 1
                    if depth > 1 and full_url not in urls:
                        nested_urls = self.discover_from_page_links(full_url, depth - 1)
                        urls.extend(nested_urls)
            
            logger.info(f"Discovered {len(urls)} URLs from page {url}")
            
        except Exception as e:
            logger.error(f"Error discovering from page {url}: {e}")
        
        return urls
    
    def get_all_starting_urls(self) -> List[str]:
        """
        Get all configured starting URLs.
        
        Returns:
            List of starting URLs
        """
        urls = []
        
        # Developer docs
        dev_url = self.config.get('odoo.developer_url')
        if dev_url:
            urls.append(dev_url)
        
        # User docs
        user_url = self.config.get('odoo.user_url')
        if user_url:
            urls.append(user_url)
        
        # Base URL
        base_url = self.config.get_base_url()
        if base_url and base_url not in urls:
            urls.append(base_url)
        
        return urls
    
    def discover_all(self, use_sitemap: bool = True, use_sidebar: bool = True) -> List[str]:
        """
        Discover all URLs using all available methods.
        
        Args:
            use_sitemap: Whether to use sitemap discovery
            use_sidebar: Whether to use sidebar discovery
            
        Returns:
            List of all discovered URLs
        """
        all_urls = []
        
        if use_sitemap:
            sitemap_urls = self.discover_from_sitemap()
            all_urls.extend(sitemap_urls)
        
        if use_sidebar:
            for start_url in self.get_all_starting_urls():
                sidebar_urls = self.discover_from_sidebar(start_url)
                all_urls.extend(sidebar_urls)
                
                # Also discover from page links
                page_urls = self.discover_from_page_links(start_url, depth=1)
                all_urls.extend(page_urls)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in all_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"Total unique URLs discovered: {len(unique_urls)}")
        return unique_urls
    
    def categorize_url(self, url: str) -> str:
        """
        Categorize a URL based on its path.
        
        Args:
            url: URL to categorize
            
        Returns:
            Category name (developer, functional, setup, or unknown)
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        categories = self.config.get_categories_config()
        
        for category, config in categories.items():
            patterns = config.get('patterns', [])
            for pattern in patterns:
                if re.match(pattern, path):
                    return category
        
        return 'unknown'
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain as base URL."""
        base_parsed = urlparse(self.base_url)
        url_parsed = urlparse(url)
        return base_parsed.netloc == url_parsed.netloc
    
    def _is_valid_doc_url(self, url: str) -> bool:
        """Check if URL is a valid documentation URL."""
        if not self._is_same_domain(url):
            return False
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Must be in documentation path
        if '/documentation/19.0' not in path:
            return False
        
        # Skip non-HTML resources
        skip_extensions = ['.pdf', '.zip', '.tar.gz', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js']
        for ext in skip_extensions:
            if path.endswith(ext):
                return False
        
        return True
    
    def filter_urls(self, urls: List[str], category: Optional[str] = None) -> List[str]:
        """
        Filter URLs by criteria.
        
        Args:
            urls: List of URLs to filter
            category: Filter by category (optional)
            
        Returns:
            Filtered list of URLs
        """
        filtered = []
        
        for url in urls:
            # Skip invalid URLs
            if not self._is_valid_doc_url(url):
                continue
            
            # Filter by category if specified
            if category:
                url_category = self.categorize_url(url)
                if url_category != category:
                    continue
            
            filtered.append(url)
        
        return filtered
