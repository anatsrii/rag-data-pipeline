"""
Vector Store
============

Generic vector database interface using ChromaDB.
Works with any embedding model.
"""

import chromadb
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """
    Generic vector store for RAG.
    
    Example:
        store = VectorStore(db_path="./chroma_db", collection_name="my_docs")
        
        # Add documents
        store.add_documents([
            {'text': 'content', 'metadata': {'source': 'example.com'}}
        ], embeddings=[[0.1, 0.2, ...]])
        
        # Search
        results = store.search(query_embedding=[0.1, 0.2, ...], n_results=5)
    """
    
    def __init__(
        self,
        db_path: str = "./chroma_db",
        collection_name: str = "documents",
        embedding_function=None
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
            logger.info(f"Connected to existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Add documents to vector store.
        
        Args:
            documents: List of {'text': str, 'metadata': dict}
            embeddings: Optional pre-computed embeddings
            
        Returns:
            True if successful
        """
        try:
            ids = []
            texts = []
            metadatas = []
            
            for i, doc in enumerate(documents):
                doc_id = doc.get('id') or f"doc_{i}"
                ids.append(doc_id)
                texts.append(doc['text'])
                metadatas.append(doc.get('metadata', {}))
            
            if embeddings:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
            else:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
            
            logger.info(f"Added {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            n_results: Number of results
            filter_dict: Optional metadata filter
            
        Returns:
            List of results with text, metadata, distance
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict
            )
            
            formatted = []
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_collection(self) -> bool:
        """Delete entire collection"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'db_path': self.db_path
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
