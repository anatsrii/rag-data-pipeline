"""
Document Chunker
================

Split documents into chunks for vector storage.
"""

from typing import List, Dict, Any
import re


class DocumentChunker:
    """
    Chunk documents with configurable size and overlap.
    
    Example:
        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.chunk_document(document_text, metadata={'source': 'example.com'})
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def chunk_document(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split document into overlapping chunks.
        
        Args:
            text: Document text
            metadata: Optional metadata to include with each chunk
            
        Returns:
            List of chunks with text and metadata
        """
        if not text:
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            # If single paragraph is too big, split it
            if paragraph_size > self.chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append(self._create_chunk(
                        current_chunk, metadata, chunk_index
                    ))
                    chunk_index += 1
                    
                    # Keep overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_size = len(overlap_text) if overlap_text else 0
                
                # Split big paragraph
                words = paragraph.split()
                current_words = []
                
                for word in words:
                    current_words.append(word)
                    if len(' '.join(current_words)) >= self.chunk_size:
                        chunks.append(self._create_chunk(
                            [' '.join(current_words)], metadata, chunk_index
                        ))
                        chunk_index += 1
                        
                        # Keep overlap words
                        overlap_words = current_words[-self.chunk_overlap//10:]  # Approximate
                        current_words = overlap_words
                
                if current_words:
                    current_chunk = [' '.join(current_words)]
                    current_size = len(current_chunk[0])
                    
            else:
                # Check if adding this paragraph exceeds chunk size
                if current_size + paragraph_size > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunks.append(self._create_chunk(
                        current_chunk, metadata, chunk_index
                    ))
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = ([overlap_text] if overlap_text else []) + [paragraph]
                    current_size = sum(len(c) for c in current_chunk)
                else:
                    current_chunk.append(paragraph)
                    current_size += paragraph_size
        
        # Don't forget last chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata, chunk_index))
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text for processing"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()
    
    def _get_overlap(self, chunks: List[str]) -> str:
        """Get overlap text from previous chunks"""
        if not chunks:
            return ""
        
        # Join last chunks until we have enough overlap
        overlap_parts = []
        total_len = 0
        
        for chunk in reversed(chunks):
            if total_len + len(chunk) <= self.chunk_overlap:
                overlap_parts.insert(0, chunk)
                total_len += len(chunk)
            else:
                # Take partial
                remaining = self.chunk_overlap - total_len
                if remaining > 0:
                    overlap_parts.insert(0, chunk[-remaining:])
                break
        
        return '\n\n'.join(overlap_parts)
    
    def _create_chunk(self, chunks: List[str], metadata: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create chunk with metadata"""
        chunk_data = {
            'text': '\n\n'.join(chunks),
            'chunk_index': index,
            'char_count': sum(len(c) for c in chunks)
        }
        
        if metadata:
            chunk_data['metadata'] = metadata
        
        return chunk_data
