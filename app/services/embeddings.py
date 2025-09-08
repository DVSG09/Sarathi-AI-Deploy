import re
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding service with a sentence transformer model"""
        try:
            self.model = SentenceTransformer(model_name)
            self.chunk_size = 512  # tokens
            self.chunk_overlap = 50  # tokens
            logger.info(f"Initialized embedding service with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            self.model = None
    
    def chunk_text(self, text: str, chunk_size: Optional[int] = None, 
                   chunk_overlap: Optional[int] = None) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        if chunk_overlap is None:
            chunk_overlap = self.chunk_overlap
        
        # Simple sentence-based chunking
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        """
        if not self.model:
            logger.warning("Embedding model not available, returning empty embeddings")
            return [[0.0] * 384] * len(texts)  # Default dimension for all-MiniLM-L6-v2
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * 384] * len(texts)
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        return self.get_embeddings([text])[0]
    
    def process_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Process content by chunking and generating embeddings
        Returns list of chunks with their embeddings
        """
        chunks = self.chunk_text(content)
        embeddings = self.get_embeddings(chunks)
        
        processed_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            processed_chunks.append({
                'text': chunk,
                'embedding': embedding,
                'chunk_index': i
            })
        
        return processed_chunks
    
    def similarity_search(self, query: str, chunks: List[Dict[str, Any]], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search between query and chunks
        """
        if not chunks:
            return []
        
        query_embedding = self.get_embedding(query)
        
        # Calculate cosine similarities
        similarities = []
        for chunk in chunks:
            if chunk.get('embedding'):
                similarity = self._cosine_similarity(query_embedding, chunk['embedding'])
                similarities.append((similarity, chunk))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in similarities[:top_k]]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def batch_process_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple feed entries in batch for efficiency
        """
        processed_entries = []
        
        for entry in entries:
            try:
                chunks = self.process_content(entry['content'])
                entry['chunks'] = chunks
                entry['chunks_count'] = len(chunks)
                processed_entries.append(entry)
            except Exception as e:
                logger.error(f"Error processing entry {entry.get('id', 'unknown')}: {e}")
                # Add entry with empty chunks
                entry['chunks'] = []
                entry['chunks_count'] = 0
                processed_entries.append(entry)
        
        return processed_entries

# Global embedding service instance
embedding_service = EmbeddingService() 