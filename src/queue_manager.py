"""
Queue Manager Module
====================

Manages URL queue, tracks crawled URLs, and prevents duplicate crawling.
"""

import json
import hashlib
from pathlib import Path
from typing import Set, List, Optional, Dict, Any
from datetime import datetime
import logging

from src.config_loader import ConfigLoader


logger = logging.getLogger(__name__)


class QueueManager:
    """Manage URL queue and track crawling progress."""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        Initialize queue manager.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config or ConfigLoader()
        
        # Initialize sets
        self.queue: List[str] = []  # URLs to crawl
        self.crawled: Set[str] = set()  # Already crawled URLs
        self.failed: Dict[str, Dict] = {}  # Failed URLs with error info
        self.in_progress: Set[str] = set()  # Currently crawling URLs
        
        # File paths
        self.cache_file = Path(self.config.get('storage.crawled_cache', './config/crawled_cache.json'))
        self.failed_file = Path(self.config.get('storage.failed_urls_log', './config/failed_urls.json'))
        
        # Load existing state
        self._load_cache()
        self._load_failed()
    
    def _load_cache(self) -> None:
        """Load crawled URLs cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.crawled = set(data.get('crawled', []))
                    logger.info(f"Loaded {len(self.crawled)} crawled URLs from cache")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.crawled = set()
    
    def _save_cache(self) -> None:
        """Save crawled URLs cache to file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'crawled': list(self.crawled),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _load_failed(self) -> None:
        """Load failed URLs from file."""
        if self.failed_file.exists():
            try:
                with open(self.failed_file, 'r', encoding='utf-8') as f:
                    self.failed = json.load(f)
                    logger.info(f"Loaded {len(self.failed)} failed URLs from log")
            except Exception as e:
                logger.error(f"Error loading failed URLs: {e}")
                self.failed = {}
    
    def _save_failed(self) -> None:
        """Save failed URLs to file."""
        try:
            self.failed_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving failed URLs: {e}")
    
    def add_to_queue(self, url: str) -> bool:
        """
        Add URL to queue if not already crawled or queued.
        
        Args:
            url: URL to add
            
        Returns:
            True if added, False if already exists
        """
        normalized_url = self._normalize_url(url)
        
        if (normalized_url in self.crawled or 
            normalized_url in self.queue or 
            normalized_url in self.in_progress):
            return False
        
        self.queue.append(normalized_url)
        return True
    
    def add_many_to_queue(self, urls: List[str]) -> int:
        """
        Add multiple URLs to queue.
        
        Args:
            urls: List of URLs to add
            
        Returns:
            Number of URLs added
        """
        added = 0
        for url in urls:
            if self.add_to_queue(url):
                added += 1
        
        logger.info(f"Added {added} new URLs to queue (skipped {len(urls) - added} duplicates)")
        return added
    
    def get_next(self) -> Optional[str]:
        """
        Get next URL from queue.
        
        Returns:
            Next URL or None if queue is empty
        """
        while self.queue:
            url = self.queue.pop(0)
            normalized = self._normalize_url(url)
            
            # Skip if already crawled
            if normalized in self.crawled:
                continue
            
            # Mark as in progress
            self.in_progress.add(normalized)
            return url
        
        return None
    
    def mark_crawled(self, url: str, metadata: Optional[Dict] = None) -> None:
        """
        Mark URL as successfully crawled.
        
        Args:
            url: URL that was crawled
            metadata: Optional metadata about the crawl
        """
        normalized = self._normalize_url(url)
        
        self.crawled.add(normalized)
        self.in_progress.discard(normalized)
        
        # Remove from failed if it was there
        if normalized in self.failed:
            del self.failed[normalized]
            self._save_failed()
        
        # Save cache periodically
        if len(self.crawled) % 10 == 0:
            self._save_cache()
    
    def mark_failed(self, url: str, error: str, retry_count: int = 0) -> None:
        """
        Mark URL as failed.
        
        Args:
            url: URL that failed
            error: Error message
            retry_count: Number of retry attempts
        """
        normalized = self._normalize_url(url)
        
        self.in_progress.discard(normalized)
        
        self.failed[normalized] = {
            'url': url,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'retry_count': retry_count
        }
        
        self._save_failed()
    
    def should_retry(self, url: str, max_retries: int = 3) -> bool:
        """
        Check if URL should be retried.
        
        Args:
            url: URL to check
            max_retries: Maximum number of retries
            
        Returns:
            True if should retry
        """
        normalized = self._normalize_url(url)
        
        if normalized not in self.failed:
            return True
        
        return self.failed[normalized].get('retry_count', 0) < max_retries
    
    def is_crawled(self, url: str) -> bool:
        """
        Check if URL has been crawled.
        
        Args:
            url: URL to check
            
        Returns:
            True if already crawled
        """
        normalized = self._normalize_url(url)
        return normalized in self.crawled
    
    def is_queued(self, url: str) -> bool:
        """
        Check if URL is in queue.
        
        Args:
            url: URL to check
            
        Returns:
            True if in queue
        """
        normalized = self._normalize_url(url)
        return normalized in self.queue
    
    def get_queue_size(self) -> int:
        """Get number of URLs in queue."""
        return len(self.queue)
    
    def get_crawled_count(self) -> int:
        """Get number of crawled URLs."""
        return len(self.crawled)
    
    def get_failed_count(self) -> int:
        """Get number of failed URLs."""
        return len(self.failed)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'queue_size': len(self.queue),
            'crawled_count': len(self.crawled),
            'failed_count': len(self.failed),
            'in_progress': len(self.in_progress),
            'total': len(self.queue) + len(self.crawled) + len(self.failed)
        }
    
    def reset_failed(self) -> List[str]:
        """
        Reset failed URLs and add them back to queue.
        
        Returns:
            List of URLs that were reset
        """
        reset_urls = []
        
        for url, info in list(self.failed.items()):
            if self.should_retry(url):
                self.add_to_queue(url)
                reset_urls.append(url)
        
        # Clear failed list
        self.failed = {}
        self._save_failed()
        
        logger.info(f"Reset {len(reset_urls)} failed URLs to queue")
        return reset_urls
    
    def clear_cache(self) -> None:
        """Clear all caches (use with caution)."""
        self.queue = []
        self.crawled = set()
        self.failed = {}
        self.in_progress = set()
        
        if self.cache_file.exists():
            self.cache_file.unlink()
        
        if self.failed_file.exists():
            self.failed_file.unlink()
        
        logger.info("Queue cache cleared")
    
    def save_state(self) -> None:
        """Save current state to disk."""
        self._save_cache()
        self._save_failed()
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent comparison.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Remove fragment
        if '#' in url:
            url = url.split('#')[0]
        
        # Remove default index.html
        if url.endswith('/index.html'):
            url = url[:-10]
        
        return url.lower()
    
    def get_url_hash(self, url: str) -> str:
        """
        Get hash of URL for identification.
        
        Args:
            url: URL to hash
            
        Returns:
            MD5 hash of URL
        """
        return hashlib.md5(url.encode()).hexdigest()[:12]
