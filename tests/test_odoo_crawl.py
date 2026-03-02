#!/usr/bin/env python3
"""
Test Crawl Odoo Documentation
==============================

ทดสอบ crawl Odoo docs แล้วเก็บข้อมูลผ่าน MCP Pipeline

Usage:
    python test_odoo_crawl.py [--limit N]
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_tools import SourceTools, SearchTool
from src.storage import SourceConfig


def test_add_source():
    """ทดสอบเพิ่ม Odoo source"""
    print("=" * 60)
    print("Test 1: Add Odoo Documentation Source")
    print("=" * 60)
    
    tools = SourceTools()
    
    # Add Odoo docs source
    result = tools.add_source(
        name="odoo_docs_test",
        urls=[
            "https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html",
            "https://www.odoo.com/documentation/17.0/developer/reference/backend/views.html",
            "https://www.odoo.com/documentation/17.0/developer/howtos/web.html",
        ],
        category="documentation",
        description="Odoo 17.0 Developer Documentation (Test)",
        chunk_size=1000,
        chunk_overlap=200
    )
    
    print(f"Result: {result}")
    return result.get("success", False)


def test_list_sources():
    """ทดสอบดูรายการ sources"""
    print("\n" + "=" * 60)
    print("Test 2: List All Sources")
    print("=" * 60)
    
    tools = SourceTools()
    sources = tools.list_sources()
    
    print(f"Found {len(sources)} sources:")
    for src in sources:
        print(f"  - {src['name']} ({src['category']}): {src['urls_count']} URLs")
    
    return sources


def test_crawl_source(limit: int = None):
    """ทดสอบ crawl source"""
    print("\n" + "=" * 60)
    print(f"Test 3: Crawl Odoo Source (limit: {limit or 'all'})")
    print("=" * 60)
    
    tools = SourceTools()
    
    # Check if source exists
    sources = tools.list_sources()
    odoo_sources = [s for s in sources if 'odoo' in s['name'].lower()]
    
    if not odoo_sources:
        print("No Odoo source found. Please run test 1 first.")
        return False
    
    source_name = odoo_sources[0]['name']
    print(f"Crawling source: {source_name}")
    
    # Get source config
    config = tools.manager.get_source_config(source_name)
    
    if limit and config:
        # Limit URLs for testing
        config.urls = config.urls[:limit]
        print(f"Limited to {len(config.urls)} URLs for testing")
    
    # Crawl
    result = tools.crawl_source(source_name)
    print(f"Crawl result: {result}")
    
    return result.get("success", False)


def test_search():
    """ทดสอบค้นหา"""
    print("\n" + "=" * 60)
    print("Test 4: Search Documents")
    print("=" * 60)
    
    search = SearchTool()
    
    # Test queries
    queries = [
        "ORM models",
        "views xml",
        "web framework",
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        try:
            results = search.search(query, n_results=3)
            print(f"  Found {len(results)} results")
            for i, r in enumerate(results[:2], 1):
                if 'error' in r:
                    print(f"  {i}. Error: {r['error']}")
                else:
                    text = r.get('text', '')[:100] + "..."
                    source = r.get('source', 'unknown')
                    print(f"  {i}. [{source}] {text}")
        except Exception as e:
            print(f"  Error: {e}")


def test_source_stats():
    """ทดสอบดูสถิติ"""
    print("\n" + "=" * 60)
    print("Test 5: Source Statistics")
    print("=" * 60)
    
    tools = SourceTools()
    sources = tools.list_sources()
    
    for src in sources:
        name = src['name']
        stats = tools.get_source_stats(name)
        print(f"\n{name}:")
        print(f"  Category: {stats.get('category', 'N/A')}")
        print(f"  URLs: {len(stats.get('urls', []))}")
        print(f"  Raw files: {stats.get('raw_files', 0)}")
        print(f"  Processed: {stats.get('processed_files', 0)}")


def main():
    parser = argparse.ArgumentParser(description="Test Odoo Crawl with MCP")
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Limit URLs to crawl for testing (default: 3)"
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Skip crawl step"
    )
    parser.add_argument(
        "--skip-search",
        action="store_true",
        help="Skip search step"
    )
    
    args = parser.parse_args()
    
    print("RAG Data Pipeline - Odoo Test")
    print("=" * 60)
    print(f"Data path: ./data")
    print(f"Limit: {args.limit} URLs")
    print("=" * 60)
    
    # Test 1: Add source
    success = test_add_source()
    if not success:
        print("\n⚠️  Add source may have failed, continuing...")
    
    # Test 2: List sources
    sources = test_list_sources()
    
    # Test 3: Crawl
    if not args.skip_crawl and sources:
        crawl_success = test_crawl_source(limit=args.limit)
        if not crawl_success:
            print("\n⚠️  Crawl failed or no data yet")
    else:
        print("\n⏭️  Skipping crawl")
    
    # Test 4: Search
    if not args.skip_search:
        test_search()
    else:
        print("\n⏭️  Skipping search")
    
    # Test 5: Stats
    test_source_stats()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check data at: ./data/sources/")
    print("2. Check vector DB at: ./data/vector_db/")
    print("3. Run MCP server: python -m src.mcp_server_v3")


if __name__ == "__main__":
    main()
