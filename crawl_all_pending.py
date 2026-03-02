#!/usr/bin/env python3
"""
Crawl All Pending Sources
==========================

Crawl all sources that haven't been crawled yet.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_tools import SourceTools

print("=== Crawl All Pending Sources ===\n")

tools = SourceTools()
sources = tools.list_sources()

# Find sources with no raw files
pending = [s for s in sources if s['raw_files'] == 0]

print(f"Found {len(pending)} pending sources:\n")
for s in pending:
    print(f"  - {s['name']}: {s['urls_count']} URLs")

print("\n" + "="*50)

# Crawl each
for src in pending:
    name = src['name']
    print(f"\n[🚀] Crawling: {name}")
    print(f"     URLs: {src['urls_count']}")
    
    result = tools.crawl_source(name)
    
    if result.get('success'):
        r = result.get('results', {}).get(name, {})
        print(f"     ✅ Done: {r.get('urls_success', 0)}/{r.get('urls_total', 0)} URLs")
        print(f"     📊 Chunks: {r.get('chunks_indexed', 0)}")
    else:
        print(f"     ❌ Failed: {result.get('error', 'Unknown')}")

print("\n" + "="*50)
print("All pending sources crawled!")
print("="*50)
