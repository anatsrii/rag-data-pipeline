#!/usr/bin/env python3
"""
Generate Quality Report from crawled documents
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    # Load metadata
    metadata_file = Path('./config/metadata.json')
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Calculate statistics
    total_docs = len(metadata)
    total_words = sum(m.get('word_count', 0) for m in metadata.values())
    avg_words = total_words // total_docs if total_docs > 0 else 0
    
    # Categories
    categories = {}
    for meta in metadata.values():
        cat = meta.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    # Generate report
    report_lines = [
        "=" * 60,
        "Odoo 19 Documentation Crawler - Quality Report",
        "=" * 60,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "📊 Statistics",
        "-" * 40,
        f"Total Documents: {total_docs}",
        f"Total Words: {total_words:,}",
        f"Average Words per Document: {avg_words:,}",
        "",
        "📁 Categories",
        "-" * 40,
    ]
    
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        report_lines.append(f"  {cat}: {count}")
    
    # Top 10 largest documents
    report_lines.extend([
        "",
        "📄 Top 10 Largest Documents",
        "-" * 40,
    ])
    sorted_docs = sorted(metadata.values(), key=lambda x: -x.get('word_count', 0))[:10]
    for doc in sorted_docs:
        report_lines.append(f"  {doc.get('title', 'Untitled')[:50]}... ({doc.get('word_count', 0):,} words)")
    
    # Bottom 10 smallest documents
    report_lines.extend([
        "",
        "📄 Top 10 Smallest Documents",
        "-" * 40,
    ])
    sorted_docs = sorted(metadata.values(), key=lambda x: x.get('word_count', 0))[:10]
    for doc in sorted_docs:
        report_lines.append(f"  {doc.get('title', 'Untitled')[:50]}... ({doc.get('word_count', 0):,} words)")
    
    report_lines.extend([
        "",
        "=" * 60,
    ])
    
    report = '\n'.join(report_lines)
    
    # Save report
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print("\n💾 Report saved to: report.txt")

if __name__ == '__main__':
    main()
