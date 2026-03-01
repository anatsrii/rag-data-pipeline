#!/usr/bin/env python3
"""
Generate metadata from crawled documents
"""

import json
import re
from pathlib import Path
from datetime import datetime

def extract_metadata_from_file(filepath):
    """Extract metadata from markdown file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return None
        
        frontmatter = frontmatter_match.group(1)
        
        # Parse metadata
        metadata = {}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"')
        
        # Count words
        markdown_content = content[frontmatter_match.end():]
        word_count = len(markdown_content.split())
        
        return {
            'source_url': metadata.get('source_url', ''),
            'title': metadata.get('title', 'Untitled'),
            'version': metadata.get('version', '19.0'),
            'category': metadata.get('category', 'unknown'),
            'word_count': word_count,
            'file_path': str(filepath),
            'last_crawled': metadata.get('last_crawled', datetime.now().isoformat())
        }
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def main():
    raw_docs_path = Path('./raw_docs')
    metadata = {}
    
    print("Generating metadata from crawled documents...")
    
    for filepath in raw_docs_path.rglob('*.md'):
        if filepath.name == '.gitkeep':
            continue
        
        meta = extract_metadata_from_file(filepath)
        if meta and meta['source_url']:
            metadata[meta['source_url']] = meta
            print(f"✓ {meta['title'][:50]}... ({meta['word_count']} words)")
    
    # Save metadata
    metadata_file = Path('./config/metadata.json')
    metadata_file.parent.mkdir(exist_ok=True)
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Metadata generated for {len(metadata)} documents")
    print(f"💾 Saved to: {metadata_file}")
    
    # Statistics
    categories = {}
    total_words = 0
    for meta in metadata.values():
        cat = meta.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
        total_words += meta.get('word_count', 0)
    
    print(f"\n📊 Statistics:")
    print(f"   Total Documents: {len(metadata)}")
    print(f"   Total Words: {total_words:,}")
    print(f"   Average Words: {total_words // len(metadata) if metadata else 0:,}")
    print(f"\n📁 Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   - {cat}: {count}")

if __name__ == '__main__':
    main()
