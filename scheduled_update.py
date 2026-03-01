#!/usr/bin/env python3
"""
Scheduled Update for Odoo 19 Documentation Crawler
===================================================

อัพเดตข้อมูลจาก Odoo Documentation แบบ manual (optional)
สำหรับผู้ที่ต้องการข้อมูลล่าสุด

Usage:
    python scheduled_update.py [options]

Options:
    --full          อัพเดตทั้งหมด (crawl + index)
    --crawl-only    crawl อย่างเดียว ไม่ index
    --index-only    index อย่างเดียว (ถ้ามีไฟล์ใหม่)
    --max-pages N   จำกัดจำนวนหน้า (default: ทั้งหมด)
    --dry-run       ทดสอบโดยไม่บันทึกจริง

Examples:
    # อัพเดตทั้งหมด
    python scheduled_update.py --full

    # crawl 100 หน้าใหม่
    python scheduled_update.py --full --max-pages 100

    # index ใหม่ทั้งหมด (ถ้าไฟล์มีปัญหา)
    python scheduled_update.py --index-only
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json


def log(message: str):
    """Print log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_crawl(max_pages: int = None, dry_run: bool = False) -> bool:
    """
    Run crawler to fetch new documents
    
    Args:
        max_pages: Maximum pages to crawl (None = all)
        dry_run: If True, don't save anything
        
    Returns:
        True if successful
    """
    log("🚀 Starting crawler...")
    
    cmd = [sys.executable, "-m", "src.main", "crawl", "--urls", "urls.txt"]
    
    if max_pages:
        cmd.extend(["--max-pages", str(max_pages)])
    
    if dry_run:
        log("   (Dry run mode - no changes will be saved)")
        return True
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode == 0:
            log("✅ Crawl completed successfully")
            return True
        else:
            log(f"❌ Crawl failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        log("❌ Crawl timeout (1 hour)")
        return False
    except Exception as e:
        log(f"❌ Crawl error: {e}")
        return False


def run_indexing(dry_run: bool = False) -> bool:
    """
    Run indexing to update vector database
    
    Args:
        dry_run: If True, don't save anything
        
    Returns:
        True if successful
    """
    if dry_run:
        log("   (Dry run - skipping indexing)")
        return True
    
    log("📊 Starting indexing...")
    
    try:
        from src.rag_engine import RAGEngine, DocumentIndexer
        
        # Initialize RAG engine
        rag = RAGEngine(db_path="E:/sandbox_claude/data/odoo19_chroma_db")
        
        # Delete old collection and recreate
        log("   Clearing old index...")
        rag.delete_collection()
        rag = RAGEngine(db_path="E:/sandbox_claude/data/odoo19_chroma_db")
        
        # Index all documents
        indexer = DocumentIndexer(rag, raw_docs_path="./raw_docs")
        indexer.index_all_documents()
        
        # Get stats
        stats = rag.get_collection_stats()
        log(f"✅ Indexing completed: {stats['total_documents']} chunks")
        
        return True
        
    except Exception as e:
        log(f"❌ Indexing error: {e}")
        return False


def update_metadata():
    """Update metadata and reports"""
    log("📝 Updating metadata...")
    
    try:
        # Generate new metadata
        subprocess.run([sys.executable, "generate_metadata.py"], 
                      capture_output=True, timeout=60)
        
        # Generate new report
        subprocess.run([sys.executable, "generate_report.py"],
                      capture_output=True, timeout=60)
        
        log("✅ Metadata updated")
        return True
        
    except Exception as e:
        log(f"❌ Metadata update error: {e}")
        return False


def save_update_log(results: dict):
    """Save update log for tracking"""
    log_file = Path("./config/update_log.json")
    
    # Load existing logs
    logs = []
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)
    
    # Add new log
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "results": results
    })
    
    # Keep only last 10 logs
    logs = logs[-10:]
    
    # Save
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Scheduled Update for Odoo 19 Documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full update (crawl + index)
  python scheduled_update.py --full
  
  # Update 100 pages only
  python scheduled_update.py --full --max-pages 100
  
  # Re-index existing files
  python scheduled_update.py --index-only
  
  # Test run (no changes)
  python scheduled_update.py --full --dry-run
        """
    )
    
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full update: crawl + index"
    )
    
    parser.add_argument(
        "--crawl-only",
        action="store_true",
        help="Crawl only, don't index"
    )
    
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Index only, don't crawl"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to crawl (default: all)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test run without saving changes"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (args.full or args.crawl_only or args.index_only):
        parser.print_help()
        sys.exit(1)
    
    # Print header
    print("=" * 60)
    print("Odoo 19 Documentation - Scheduled Update")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Action: {' + '.join(filter(None, [
        'crawl' if (args.full or args.crawl_only) else '',
        'index' if (args.full or args.index_only) else ''
    ]))}")
    print("=" * 60)
    
    results = {
        "crawl_success": False,
        "index_success": False,
        "metadata_success": False
    }
    
    # Run crawl
    if args.full or args.crawl_only:
        results["crawl_success"] = run_crawl(args.max_pages, args.dry_run)
        
        if not results["crawl_success"] and not args.dry_run:
            log("⚠️  Crawl failed, skipping indexing")
            save_update_log(results)
            sys.exit(1)
    
    # Run indexing
    if args.full or args.index_only:
        results["index_success"] = run_indexing(args.dry_run)
        
        if not results["index_success"] and not args.dry_run:
            log("⚠️  Indexing failed")
            save_update_log(results)
            sys.exit(1)
    
    # Update metadata
    if not args.dry_run and (results["crawl_success"] or results["index_success"]):
        results["metadata_success"] = update_metadata()
    
    # Save log
    if not args.dry_run:
        save_update_log(results)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Update Summary")
    print("=" * 60)
    print(f"Crawl:     {'✅' if results['crawl_success'] else '❌'}")
    print(f"Index:     {'✅' if results['index_success'] else '❌'}")
    print(f"Metadata:  {'✅' if results['metadata_success'] else '❌'}")
    print("=" * 60)
    
    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
    else:
        print("\n✅ Update completed!")


if __name__ == "__main__":
    main()
