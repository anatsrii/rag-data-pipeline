#!/usr/bin/env python3
"""
Test RAG - Odoo 19 Documentation
"""

import sys
sys.path.insert(0, 'src')

from rag_engine import RAGEngine

print('=' * 60)
print('Testing RAG - Odoo 19 Documentation')
print('=' * 60)

rag = RAGEngine(db_path='E:/sandbox_claude/data/odoo19_chroma_db')

stats = rag.get_collection_stats()
print(f'\n📊 Database Stats:')
print(f'   Total chunks: {stats["total_documents"]}')
print(f'   Embedding dimension: {stats["embedding_dimension"]}')

# Test 1: ค้นหาเรื่องสร้าง module
print('\n' + '=' * 60)
print('Test 1: สร้าง Odoo module ใหม่')
print('=' * 60)
results = rag.search('how to create a new module in Odoo', n_results=3)

for i, r in enumerate(results, 1):
    print(f'\n{i}. {r["metadata"].get("title", "Untitled")}')
    print(f'   Category: {r["metadata"].get("category", "unknown")}')
    print(f'   Relevance: {1 - r["distance"]:.2%}')
    print(f'   Preview: {r["document"][:150]}...')

# Test 2: ORM API
print('\n' + '=' * 60)
print('Test 2: ORM API - Models and Fields')
print('=' * 60)
results = rag.search('ORM API models fields Char Integer Boolean', n_results=3)

for i, r in enumerate(results, 1):
    print(f'\n{i}. {r["metadata"].get("title", "Untitled")}')
    print(f'   Relevance: {1 - r["distance"]:.2%}')

# Test 3: Security
print('\n' + '=' * 60)
print('Test 3: Security - Access Rights')
print('=' * 60)
results = rag.search('security access rights ir.model.access.csv groups', n_results=3)

for i, r in enumerate(results, 1):
    print(f'\n{i}. {r["metadata"].get("title", "Untitled")}')
    print(f'   Relevance: {1 - r["distance"]:.2%}')

# Test 4: Views
print('\n' + '=' * 60)
print('Test 4: Views - Tree, Form, Search')
print('=' * 60)
results = rag.search('views tree form search xml arch', n_results=3)

for i, r in enumerate(results, 1):
    print(f'\n{i}. {r["metadata"].get("title", "Untitled")}')
    print(f'   Relevance: {1 - r["distance"]:.2%}')

# Test 5: ภาษาไทย
print('\n' + '=' * 60)
print('Test 5: ค้นหาภาษาไทย - สร้างโมดูล')
print('=' * 60)
results = rag.search('วิธีสร้างโมดูลใหม่ใน Odoo', n_results=3)

for i, r in enumerate(results, 1):
    print(f'\n{i}. {r["metadata"].get("title", "Untitled")}')
    print(f'   Relevance: {1 - r["distance"]:.2%}')

print('\n' + '=' * 60)
print('✅ All tests completed!')
print('=' * 60)
