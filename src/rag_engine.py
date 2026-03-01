"""
RAG Engine for Odoo 19 Documentation
=====================================

Provides vector search and retrieval capabilities for the crawled documentation.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np


class RAGEngine:
    """RAG Engine for querying Odoo documentation."""
    
    def __init__(self, 
                 collection_name: str = "odoo_docs",
                 db_path: str = "./chroma_db",
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG Engine.
        
        Args:
            collection_name: Name of the ChromaDB collection
            db_path: Path to ChromaDB storage
            model_name: Sentence transformer model for embeddings
        """
        self.collection_name = collection_name
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Odoo 19 Documentation"}
        )
        
        # Initialize embedding model
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        
    def embed_text(self, text: str) -> List[float]:
        """
        Create embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add_document(self, 
                     doc_id: str, 
                     text: str, 
                     metadata: Dict[str, Any],
                     chunk_size: int = 500,
                     chunk_overlap: int = 100) -> None:
        """
        Add document to vector store with chunking.
        
        Args:
            doc_id: Unique document ID
            text: Document text
            metadata: Document metadata
            chunk_size: Size of each chunk in words
            chunk_overlap: Overlap between chunks in words
        """
        # Split text into chunks
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        
        # Add each chunk
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            embedding = self.embed_text(chunk)
            
            # Prepare metadata
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "doc_id": doc_id
            }
            
            # Add to collection
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[chunk_metadata]
            )
    
    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to split
            chunk_size: Chunk size in words
            chunk_overlap: Overlap in words
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        if len(words) <= chunk_size:
            return [text]
        
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start += chunk_size - chunk_overlap
        
        return chunks
    
    def search(self, 
               query: str, 
               n_results: int = 5,
               filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of search results with metadata
        """
        # Create query embedding
        query_embedding = self.embed_text(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result = {
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            }
            formatted_results.append(result)
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Dictionary with statistics
        """
        count = self.collection.count()
        return {
            "total_documents": count,
            "collection_name": self.collection_name,
            "embedding_dimension": self.embedding_dim
        }
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
        print(f"Collection '{self.collection_name}' deleted.")


class DocumentIndexer:
    """Index documents from raw_docs folder."""
    
    def __init__(self, rag_engine: RAGEngine, raw_docs_path: str = "./raw_docs"):
        """
        Initialize document indexer.
        
        Args:
            rag_engine: RAG Engine instance
            raw_docs_path: Path to raw documents
        """
        self.rag_engine = rag_engine
        self.raw_docs_path = Path(raw_docs_path)
    
    def index_all_documents(self) -> None:
        """Index all documents in raw_docs folder."""
        md_files = list(self.raw_docs_path.rglob("*.md"))
        print(f"Found {len(md_files)} markdown files to index...")
        
        for i, filepath in enumerate(md_files, 1):
            if filepath.name == '.gitkeep':
                continue
            
            print(f"[{i}/{len(md_files)}] Indexing: {filepath.name}")
            
            try:
                self._index_single_document(filepath)
            except Exception as e:
                print(f"  Error indexing {filepath.name}: {e}")
        
        print("\n✅ Indexing complete!")
        stats = self.rag_engine.get_collection_stats()
        print(f"Total chunks indexed: {stats['total_documents']}")
    
    def _index_single_document(self, filepath: Path) -> None:
        """Index a single document."""
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter and content
        import re
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        
        metadata = {}
        text_content = content
        
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            text_content = content[frontmatter_match.end():]
            
            # Parse frontmatter
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip().strip('"')
        
        # Generate doc_id from filename
        doc_id = filepath.stem
        
        # Add to RAG engine
        self.rag_engine.add_document(
            doc_id=doc_id,
            text=text_content,
            metadata={
                **metadata,
                "filename": filepath.name,
                "filepath": str(filepath)
            }
        )


if __name__ == "__main__":
    # Example usage
    print("Initializing RAG Engine...")
    rag = RAGEngine()
    
    print("\nIndexing documents...")
    indexer = DocumentIndexer(rag)
    indexer.index_all_documents()
    
    print("\nTesting search...")
    results = rag.search("how to create a new module in Odoo", n_results=3)
    
    print("\nSearch results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['metadata'].get('title', 'Untitled')}")
        print(f"   Source: {result['metadata'].get('source_url', 'N/A')}")
        print(f"   Distance: {result['distance']:.4f}")
        print(f"   Preview: {result['document'][:200]}...")
