#!/usr/bin/env python3
"""
RAG Query Tool for Odoo 19 Documentation
=========================================

Query the vector database for relevant documentation.
"""

import sys
from src.rag_engine import RAGEngine


def main():
    """Main query interface."""
    print("=" * 60)
    print("Odoo 19 Documentation RAG Query")
    print("=" * 60)
    
    # Initialize RAG engine
    print("\nLoading RAG engine...")
    rag = RAGEngine()
    
    # Show stats
    stats = rag.get_collection_stats()
    print(f"\n📊 Database Stats:")
    print(f"   Total chunks: {stats['total_documents']}")
    print(f"   Embedding dimension: {stats['embedding_dimension']}")
    
    print("\n" + "=" * 60)
    print("Enter your query (or 'quit' to exit):")
    print("=" * 60)
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not query:
                continue
            
            print("\nSearching...")
            results = rag.search(query, n_results=5)
            
            print(f"\n📄 Found {len(results)} relevant documents:\n")
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                print(f"{i}. {metadata.get('title', 'Untitled')}")
                print(f"   Category: {metadata.get('category', 'unknown')}")
                print(f"   Source: {metadata.get('source_url', 'N/A')}")
                if result['distance'] is not None:
                    print(f"   Relevance: {1 - result['distance']:.2%}")
                print(f"   Preview: {result['document'][:200]}...")
                print()
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
