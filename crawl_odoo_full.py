#!/usr/bin/env python3
"""
Crawl Odoo Documentation - Full Version
========================================

Crawl Odoo 17.0 documentation completely and index to RAG.
Run this in background as it takes time.

Usage:
    python crawl_odoo_full.py [--max-pages N] [--category CAT]

Example:
    # Crawl developer docs only
    python crawl_odoo_full.py --max-pages 200 --category developer
    
    # Crawl everything
    python crawl_odoo_full.py --max-pages 1000
"""

import argparse
import sys
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_tools import SourceTools
from src.crawler import URLDiscovery


def log(message: str):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()


def save_progress(data: dict, filename: str = "crawl_progress.json"):
    """Save crawl progress"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def load_progress(filename: str = "crawl_progress.json") -> dict:
    """Load crawl progress"""
    if Path(filename).exists():
        with open(filename, 'r') as f:
            return json.load(f)
    return {}


def crawl_odoo_documentation(
    max_pages: int = 200,
    category_filter: str = None,
    resume: bool = False
):
    """
    Complete crawl of Odoo documentation.
    
    Args:
        max_pages: Maximum pages to crawl
        category_filter: 'developer', 'applications', or None for all
        resume: Resume from previous crawl
    """
    
    log("=" * 70)
    log("Odoo Documentation Crawler - Full Version")
    log("=" * 70)
    log(f"Max pages: {max_pages}")
    log(f"Category: {category_filter or 'all'}")
    log(f"Resume: {resume}")
    log("=" * 70)
    
    # Check for resume
    progress = load_progress() if resume else {}
    
    if progress and resume:
        log(f"Resuming from previous crawl...")
        log(f"Previously found: {progress.get('urls_found', 0)} URLs")
        urls = progress.get('urls', [])
    else:
        # Step 1: Discover URLs
        log("\n[Step 1/3] Discovering URLs...")
        
        discovery = URLDiscovery(delay=1.5)  # Be nice to server
        
        # Start URLs based on category
        if category_filter == "developer":
            start_urls = ['https://www.odoo.com/documentation/17.0/developer/']
        elif category_filter == "applications":
            start_urls = ['https://www.odoo.com/documentation/17.0/applications/']
        else:
            start_urls = [
                'https://www.odoo.com/documentation/17.0/developer/',
                'https://www.odoo.com/documentation/17.0/applications/',
                'https://www.odoo.com/documentation/17.0/administration/'
            ]
        
        all_urls = set()
        
        for start_url in start_urls:
            log(f"Crawling from: {start_url}")
            urls = discovery.from_crawl(
                start_url=start_url,
                max_pages=max_pages // len(start_urls),
                same_domain=True,
                allowed_paths=['/documentation/17.0/']
            )
            all_urls.update(urls)
            log(f"  Found {len(urls)} URLs from this branch")
            time.sleep(2)  # Delay between branches
        
        urls = list(all_urls)
        log(f"\nTotal unique URLs found: {len(urls)}")
        
        # Save progress
        save_progress({
            'urls': urls,
            'urls_found': len(urls),
            'timestamp': datetime.now().isoformat()
        })
    
    if not urls:
        log("No URLs found!")
        return False
    
    # Step 2: Create Source
    log("\n[Step 2/3] Creating source...")
    
    tools = SourceTools()
    
    source_name = f"odoo17_{category_filter or 'full'}"
    
    # Check if source exists
    existing = tools.list_sources()
    if any(s['name'] == source_name for s in existing):
        log(f"Source '{source_name}' already exists, deleting...")
        tools.delete_source(source_name)
    
    result = tools.add_source(
        name=source_name,
        urls=urls,
        category=category_filter or "odoo",
        description=f"Odoo 17.0 Documentation ({category_filter or 'full'}) - {len(urls)} pages",
        chunk_size=1000,
        chunk_overlap=200
    )
    
    if not result.get('success'):
        log(f"Failed to create source: {result.get('error')}")
        return False
    
    log(f"Source '{source_name}' created with {len(urls)} URLs")
    
    # Step 3: Crawl and Index
    log("\n[Step 3/3] Crawling and indexing...")
    log("This may take a while...")
    
    crawl_result = tools.crawl_source(source_name)
    
    if crawl_result.get('success'):
        results = crawl_result.get('results', {})
        log("\n" + "=" * 70)
        log("CRAWL COMPLETE!")
        log("=" * 70)
        log(f"Source: {source_name}")
        log(f"URLs total: {results.get('urls_total', 0)}")
        log(f"URLs success: {results.get('urls_success', 0)}")
        log(f"Chunks indexed: {results.get('chunks_indexed', 0)}")
        log("=" * 70)
        
        # Update progress
        save_progress({
            'urls': urls,
            'urls_found': len(urls),
            'source_name': source_name,
            'crawl_complete': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    else:
        log(f"Crawl failed: {crawl_result.get('error')}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Crawl Odoo Documentation for RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Crawl developer docs (200 pages)
    python crawl_odoo_full.py --max-pages 200 --category developer
    
    # Crawl everything (1000 pages)
    python crawl_odoo_full.py --max-pages 1000
    
    # Resume previous crawl
    python crawl_odoo_full.py --resume
        """
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum pages to crawl (default: 200)"
    )
    
    parser.add_argument(
        "--category",
        choices=["developer", "applications", "administration"],
        default=None,
        help="Crawl only specific category"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous crawl"
    )
    
    args = parser.parse_args()
    
    # Run crawl
    success = crawl_odoo_documentation(
        max_pages=args.max_pages,
        category_filter=args.category,
        resume=args.resume
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
