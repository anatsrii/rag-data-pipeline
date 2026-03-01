"""
Odoo 19 Documentation Crawler - Main Entry Point
================================================

Main orchestrator for the Odoo 19 documentation crawling system.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import ConfigLoader
from url_discovery import URLDiscovery
from queue_manager import QueueManager
from content_extractor import ContentExtractor
from crawler_engine import CrawlerEngine
from metadata_manager import MetadataManager


def setup_logging(config: ConfigLoader) -> None:
    """
    Setup logging configuration.
    
    Args:
        config: Configuration loader
    """
    log_config = config.get_logging_config()
    level = getattr(logging, log_config.get('level', 'INFO'))
    
    # Create formatter
    formatter = logging.Formatter(
        log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    if log_config.get('console', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    log_file = log_config.get('file')
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def discover_command(args) -> None:
    """Handle discover command."""
    print("🔍 Discovering URLs from Odoo 19 Documentation...")
    
    config = ConfigLoader(args.config)
    url_discovery = URLDiscovery(config)
    
    # Discover URLs
    urls = url_discovery.discover_all(
        use_sitemap=args.sitemap,
        use_sidebar=args.sidebar
    )
    
    # Filter by category if specified
    if args.category:
        urls = url_discovery.filter_urls(urls, category=args.category)
    
    print(f"\n✅ Discovered {len(urls)} URLs")
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        print(f"💾 Saved to: {output_path}")
    
    # Print sample URLs
    if args.verbose:
        print("\n📋 Sample URLs:")
        for url in urls[:10]:
            print(f"  - {url}")
        if len(urls) > 10:
            print(f"  ... and {len(urls) - 10} more")


def crawl_command(args) -> None:
    """Handle crawl command."""
    print("🚀 Starting Odoo 19 Documentation Crawler...")
    
    config = ConfigLoader(args.config)
    
    # Ensure directories exist
    config.ensure_directories()
    
    # Setup logging
    setup_logging(config)
    
    # Initialize crawler
    crawler = CrawlerEngine(config)
    
    # Get URLs to crawl
    urls = None
    if args.urls:
        # Read from file
        urls_file = Path(args.urls)
        if urls_file.exists():
            with open(urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            print(f"📄 Loaded {len(urls)} URLs from {urls_file}")
        else:
            print(f"❌ URLs file not found: {urls_file}")
            return
    elif args.discover:
        # Auto-discover URLs
        print("🔍 Auto-discovering URLs...")
        url_discovery = URLDiscovery(config)
        urls = url_discovery.discover_all()
        print(f"✅ Discovered {len(urls)} URLs")
    
    # Run crawler
    try:
        stats = asyncio.run(crawler.run(
            urls=urls,
            max_pages=args.max_pages
        ))
        
        # Print statistics
        print("\n" + "=" * 60)
        print("📊 Crawling Statistics")
        print("=" * 60)
        print(f"Total Pages: {stats.get('total', 0)}")
        print(f"Successful: {stats.get('success', 0)} ✅")
        print(f"Failed: {stats.get('failed', 0)} ❌")
        print(f"Skipped: {stats.get('skipped', 0)} ⏭️")
        
        if stats.get('duration_seconds'):
            print(f"Duration: {stats['duration_seconds']:.1f} seconds")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️ Crawling interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during crawling: {e}")
        raise


def status_command(args) -> None:
    """Handle status command."""
    config = ConfigLoader(args.config)
    
    queue_manager = QueueManager(config)
    metadata_manager = MetadataManager(config)
    
    print("=" * 60)
    print("📊 Crawler Status")
    print("=" * 60)
    
    # Queue statistics
    queue_stats = queue_manager.get_stats()
    print("\n📝 Queue Status:")
    print(f"  Queue Size: {queue_stats['queue_size']}")
    print(f"  Crawled: {queue_stats['crawled_count']}")
    print(f"  Failed: {queue_stats['failed_count']}")
    
    # Metadata statistics
    meta_stats = metadata_manager.get_statistics()
    if meta_stats['total_documents'] > 0:
        print("\n📁 Documents:")
        print(f"  Total: {meta_stats['total_documents']}")
        print(f"  Total Words: {meta_stats['total_words']:,}")
        print(f"  Average Quality: {meta_stats['average_quality']:.1f}/100")
        
        print("\n📂 Categories:")
        for cat, count in meta_stats['categories'].items():
            print(f"  - {cat}: {count}")
    
    print("\n" + "=" * 60)


def report_command(args) -> None:
    """Handle report command."""
    config = ConfigLoader(args.config)
    metadata_manager = MetadataManager(config)
    
    # Generate and print report
    report = metadata_manager.generate_report()
    print(report)
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n💾 Report saved to: {output_path}")


def reset_command(args) -> None:
    """Handle reset command."""
    config = ConfigLoader(args.config)
    
    print("⚠️  This will reset the crawler state.")
    
    if args.force:
        confirm = 'y'
    else:
        confirm = input("Are you sure? (y/N): ").lower()
    
    if confirm == 'y':
        queue_manager = QueueManager(config)
        queue_manager.clear_cache()
        
        # Clear metadata
        metadata_db = Path(config.get('storage.metadata_db', './config/metadata.json'))
        if metadata_db.exists():
            metadata_db.unlink()
        
        print("✅ Crawler state reset successfully")
    else:
        print("❌ Cancelled")


def test_command(args) -> None:
    """Handle test command - test extraction on single URL."""
    print(f"🧪 Testing extraction on: {args.url}")
    
    config = ConfigLoader(args.config)
    setup_logging(config)
    
    import requests
    from bs4 import BeautifulSoup
    
    # Fetch URL
    try:
        response = requests.get(
            args.url,
            headers={'User-Agent': config.get_user_agent()},
            timeout=30
        )
        response.raise_for_status()
        
        print(f"✅ Fetched page ({len(response.text)} chars)")
        
        # Extract content
        extractor = ContentExtractor(config)
        content = extractor.extract_content(response.text, args.url)
        
        if content:
            print(f"\n📄 Extraction Results:")
            print(f"  Title: {content['title']}")
            print(f"  Word Count: {content['word_count']}")
            print(f"  Headings: {len(content['headings'])}")
            print(f"\n📋 Metadata:")
            for key, value in content['metadata'].items():
                print(f"  {key}: {value}")
            
            if args.verbose:
                print(f"\n📝 Content Preview (first 500 chars):")
                print("-" * 60)
                print(content['markdown'][:500])
                print("-" * 60)
            
            # Save if requested
            if args.save:
                output_path = Path(args.save)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                extractor.save_markdown(content, output_path)
                print(f"\n💾 Saved to: {output_path}")
        else:
            print("❌ Failed to extract content")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Odoo 19 Documentation Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover URLs
  python -m src.main discover --output urls.txt

  # Crawl with auto-discovery
  python -m src.main crawl --discover --max-pages 100

  # Crawl from URL list
  python -m src.main crawl --urls urls.txt

  # Check status
  python -m src.main status

  # Generate report
  python -m src.main report --output report.txt

  # Test single URL
  python -m src.main test https://www.odoo.com/documentation/19.0/developer.html --save test.md
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='./config/config.yaml',
        help='Path to configuration file (default: ./config/config.yaml)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser(
        'discover',
        help='Discover URLs from Odoo documentation'
    )
    discover_parser.add_argument(
        '--sitemap', '-s',
        action='store_true',
        default=True,
        help='Use sitemap for discovery'
    )
    discover_parser.add_argument(
        '--sidebar', '-b',
        action='store_true',
        default=True,
        help='Use sidebar navigation for discovery'
    )
    discover_parser.add_argument(
        '--category', '-cat',
        choices=['developer', 'functional', 'setup'],
        help='Filter by category'
    )
    discover_parser.add_argument(
        '--output', '-o',
        help='Save discovered URLs to file'
    )
    discover_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print discovered URLs'
    )
    discover_parser.set_defaults(func=discover_command)
    
    # Crawl command
    crawl_parser = subparsers.add_parser(
        'crawl',
        help='Start crawling documents'
    )
    crawl_parser.add_argument(
        '--urls', '-u',
        help='File containing URLs to crawl'
    )
    crawl_parser.add_argument(
        '--discover', '-d',
        action='store_true',
        help='Auto-discover URLs before crawling'
    )
    crawl_parser.add_argument(
        '--max-pages', '-m',
        type=int,
        help='Maximum number of pages to crawl'
    )
    crawl_parser.set_defaults(func=crawl_command)
    
    # Status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show crawler status'
    )
    status_parser.set_defaults(func=status_command)
    
    # Report command
    report_parser = subparsers.add_parser(
        'report',
        help='Generate quality report'
    )
    report_parser.add_argument(
        '--output', '-o',
        help='Save report to file'
    )
    report_parser.set_defaults(func=report_command)
    
    # Reset command
    reset_parser = subparsers.add_parser(
        'reset',
        help='Reset crawler state (clears cache)'
    )
    reset_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation'
    )
    reset_parser.set_defaults(func=reset_command)
    
    # Test command
    test_parser = subparsers.add_parser(
        'test',
        help='Test extraction on single URL'
    )
    test_parser.add_argument(
        'url',
        help='URL to test'
    )
    test_parser.add_argument(
        '--save', '-s',
        help='Save extracted content to file'
    )
    test_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show content preview'
    )
    test_parser.set_defaults(func=test_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
