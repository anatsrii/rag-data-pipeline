#!/usr/bin/env python3
"""
Crawl Odoo 18.0 Documentation
==============================

Crawl latest Odoo 18 docs and add to RAG.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_tools import SourceTools
from src.crawler import URLDiscovery

print("=== Crawl Odoo 18.0 Documentation ===\n")

# Discover URLs
print("[Step 1/3] Discovering URLs...")
discovery = URLDiscovery(delay=1.5)

urls = discovery.from_crawl(
    start_url='https://www.odoo.com/documentation/18.0/developer/',
    max_pages=50,
    same_domain=True,
    allowed_paths=['/documentation/18.0/']
)

print(f"Found {len(urls)} URLs\n")

# Create source
print("[Step 2/3] Creating source...")
tools = SourceTools()

# Delete if exists
existing = tools.list_sources()
if any(s['name'] == 'odoo18_developer' for s in existing):
    print("Source exists, deleting old...")
    tools.delete_source('odoo18_developer')

result = tools.add_source(
    name='odoo18_developer',
    urls=urls,
    category='developer',
    description='Odoo 18.0 Developer Documentation',
    chunk_size=1000
)

if result['success']:
    print(f"Source created: {result['name']}\n")
    
    # Crawl
    print("[Step 3/3] Crawling and indexing...")
    crawl_result = tools.crawl_source('odoo18_developer')
    
    if crawl_result['success']:
        r = crawl_result['results']
        print(f"\n✅ Complete!")
        print(f"   URLs: {r.get('urls_success', 0)}/{r.get('urls_total', 0)}")
        print(f"   Chunks: {r.get('chunks_indexed', 0)}")
    else:
        print(f"❌ Crawl failed: {crawl_result.get('error')}")
else:
    print(f"❌ Failed: {result.get('error')}")
