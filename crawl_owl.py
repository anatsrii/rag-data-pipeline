#!/usr/bin/env python3
"""
Crawl OWL Framework Documentation
==================================

Crawl OWL docs from GitHub and official sources.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_tools import SourceTools
from src.crawler import URLDiscovery

print("=== Crawl OWL Framework ===\n")

# URLs สำคัญของ OWL
owl_urls = [
    # GitHub README and docs
    "https://github.com/odoo/owl",
    "https://github.com/odoo/owl/blob/master/README.md",
    "https://github.com/odoo/owl/tree/master/doc",
    
    # Official docs
    "https://github.com/odoo/owl/blob/master/doc/readme.md",
    "https://github.com/odoo/owl/blob/master/doc/owl.md",
    "https://github.com/odoo/owl/blob/master/doc/components.md",
    "https://github.com/odoo/owl/blob/master/doc/hooks.md",
    "https://github.com/odoo/owl/blob/master/doc/reactivity.md",
    "https://github.com/odoo/owl/blob/master/doc/templates.md",
    "https://github.com/odoo/owl/blob/master/doc/slots.md",
    "https://github.com/odoo/owl/blob/master/doc/props.md",
    "https://github.com/odoo/owl/blob/master/doc/events.md",
    "https://github.com/odoo/owl/blob/master/doc/lifecycle.md",
    "https://github.com/odoo/owl/blob/master/doc/router.md",
    "https://github.com/odoo/owl/blob/master/doc/environment.md",
    "https://github.com/odoo/owl/blob/master/doc/testing.md",
    
    # Examples
    "https://github.com/odoo/owl/tree/master/examples",
    "https://github.com/odoo/owl/tree/master/examples/counter",
    "https://github.com/odoo/owl/tree/master/examples/todo_list",
    "https://github.com/odoo/owl/tree/master/examples/form_validation",
    
    # Playground
    "https://odoo.github.io/owl/playground/",
]

print(f"[Step 1/2] Preparing {len(owl_urls)} URLs...")

# Create source
tools = SourceTools()

# Delete if exists
existing = tools.list_sources()
if any(s['name'] == 'owl_framework' for s in existing):
    print("Source exists, deleting old...")
    tools.delete_source('owl_framework')

print("[Step 2/2] Creating source and crawling...")

result = tools.add_source(
    name='owl_framework',
    urls=owl_urls,
    category='frontend',
    description='OWL Framework - Odoo JavaScript Framework',
    chunk_size=800
)

if result['success']:
    print(f"✅ Source created: {result['name']}")
    print(f"   URLs: {result['urls_count']}")
    print("\nRun 'python -m src.mcp_server_full' to crawl and index")
else:
    print(f"❌ Failed: {result.get('error')}")
