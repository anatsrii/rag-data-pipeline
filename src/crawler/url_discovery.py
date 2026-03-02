"""
URL Discovery
=============

Discover URLs from sitemaps, navigation, or recursive crawling.
"""

import requests
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLDiscovery:
    """
    Discover URLs from various sources.
    
    Usage:
        discovery = URLDiscovery(delay=1.0)
        
        # From sitemap
        urls = discovery.from_sitemap("https://example.com/sitemap.xml")
        
        # From recursive crawling
        urls = discovery.from_crawl("https://example.com", max_pages=100)
        
        # From navigation/sidebar
        urls = discovery.from_navigation("https://example.com/docs")
    """
    
    def __init__(self, delay: float = 1.0, timeout: int = 30):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG-Data-Pipeline/1.0 (URL Discovery)'
        })
    
    def from_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Extract URLs from XML sitemap.
        
        Args:
            sitemap_url: URL of sitemap.xml
            
        Returns:
            List of URLs
        """
        logger.info(f"Fetching sitemap: {sitemap_url}")
        
        try:
            response = self.session.get(sitemap_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle sitemap index (multiple sitemaps)
            urls = []
            
            # Try different namespaces
            namespaces = [
                {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'},
                {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.84'},
                {}  # No namespace
            ]
            
            for ns in namespaces:
                # Look for URLs in sitemap
                locs = root.findall('.//ns:loc', ns) or root.findall('.//loc')
                
                for loc in locs:
                    url = loc.text.strip() if loc.text else ""
                    if url and url not in urls:
                        urls.append(url)
                
                if urls:
                    break
            
            logger.info(f"Found {len(urls)} URLs from sitemap")
            return urls
            
        except Exception as e:
            logger.error(f"Failed to parse sitemap: {e}")
            return []
    
    def from_crawl(
        self,
        start_url: str,
        max_pages: int = 100,
        same_domain: bool = True,
        allowed_paths: Optional[List[str]] = None
    ) -> List[str]:
        """
        Discover URLs by crawling from start URL.
        
        Args:
            start_url: URL to start crawling
            max_pages: Maximum pages to crawl
            same_domain: Only crawl same domain
            allowed_paths: Only crawl paths containing these strings
            
        Returns:
            List of discovered URLs
        """
        logger.info(f"Starting crawl from: {start_url} (max: {max_pages})")
        
        discovered = set()
        to_visit = [start_url]
        
        base_domain = urlparse(start_url).netloc
        
        while to_visit and len(discovered) < max_pages:
            url = to_visit.pop(0)
            
            if url in discovered:
                continue
            
            try:
                logger.info(f"Crawling: {url}")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                discovered.add(url)
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    # Parse URL
                    parsed = urlparse(full_url)
                    
                    # Skip non-HTTP
                    if parsed.scheme not in ('http', 'https'):
                        continue
                    
                    # Skip fragments
                    full_url = full_url.split('#')[0]
                    
                    # Check same domain
                    if same_domain and parsed.netloc != base_domain:
                        continue
                    
                    # Check allowed paths
                    if allowed_paths:
                        if not any(p in parsed.path for p in allowed_paths):
                            continue
                    
                    # Skip common non-content URLs
                    skip_extensions = ('.pdf', '.jpg', '.png', '.gif', '.css', '.js', '.zip')
                    if full_url.lower().endswith(skip_extensions):
                        continue
                    
                    if full_url not in discovered and full_url not in to_visit:
                        to_visit.append(full_url)
                
                # Respect delay
                time.sleep(self.delay)
                
            except Exception as e:
                logger.warning(f"Failed to crawl {url}: {e}")
                continue
        
        logger.info(f"Crawl complete: {len(discovered)} URLs discovered")
        return list(discovered)
    
    def from_navigation(
        self,
        url: str,
        nav_selector: str = "nav, .sidebar, .toc, .menu",
        link_selector: str = "a[href]"
    ) -> List[str]:
        """
        Extract URLs from navigation/sidebar.
        
        Args:
            url: Page URL with navigation
            nav_selector: CSS selector for navigation container
            link_selector: CSS selector for links
            
        Returns:
            List of URLs
        """
        logger.info(f"Extracting navigation from: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            urls = []
            
            # Find navigation containers
            navs = soup.select(nav_selector)
            
            if not navs:
                # Fallback: get all links
                navs = [soup]
            
            for nav in navs:
                for link in nav.select(link_selector):
                    href = link.get('href', '')
                    if href:
                        full_url = urljoin(url, href)
                        if full_url not in urls:
                            urls.append(full_url)
            
            logger.info(f"Found {len(urls)} URLs from navigation")
            return urls
            
        except Exception as e:
            logger.error(f"Failed to extract navigation: {e}")
            return []
    
    def filter_urls(
        self,
        urls: List[str],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_urls: Optional[int] = None
    ) -> List[str]:
        """
        Filter URLs by patterns.
        
        Args:
            urls: List of URLs to filter
            include_patterns: Only include URLs containing these
            exclude_patterns: Exclude URLs containing these
            max_urls: Limit number of URLs
            
        Returns:
            Filtered URLs
        """
        filtered = urls
        
        # Include patterns
        if include_patterns:
            filtered = [
                u for u in filtered
                if any(p in u for p in include_patterns)
            ]
        
        # Exclude patterns
        if exclude_patterns:
            filtered = [
                u for u in filtered
                if not any(p in u for p in exclude_patterns)
            ]
        
        # Limit
        if max_urls:
            filtered = filtered[:max_urls]
        
        return filtered
