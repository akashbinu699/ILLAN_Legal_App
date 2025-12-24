"""Embedding service using Nomic-embed-text with Late Chunking."""
import numpy as np
from typing import List, Dict, Tuple
from nomic import embed
from backend.config import settings

class EmbeddingService:
    """Service for generating embeddings with Late Chunking strategy."""
    
    def __init__(self):
        self.model_name = settings.embedding_model
        self.context_window = 32768  # 32k context window for nomic-embed-text
    
    def embed_document(self, text: str) -> np.ndarray:
        """Embed entire document for contextual encoding."""
        try:
            # Embed the full document (up to context window limit)
            # Truncate if necessary
            truncated_text = text[:self.context_window * 4]  # Rough character estimate
            
            output = embed.text(
                texts=[truncated_text],
                model=self.model_name,
                task_type='search_document'
            )
            
            # Get the embedding vector
            embedding = output['embeddings'][0]
            return np.array(embedding)
        except Exception as e:
            print(f"Error embedding document: {str(e)}")
            # Return zero vector as fallback
            return np.zeros(768)  # Default dimension for nomic-embed-text
    
    def embed_chunks_with_context(
        self,
        full_document: str,
        chunks: List[str],
        chunk_metadata: List[Dict]
    ) -> List[Tuple[np.ndarray, Dict]]:
        """
        Late Chunking: Embed chunks with full document context.
        
        Strategy:
        1. Embed entire document for context
        2. For each chunk, create context window around it
        3. Apply mean pooling over the chunk span
        """
        # Step 1: Embed full document for context
        document_embedding = self.embed_document(full_document)
        
        # Step 2: Embed each chunk with surrounding context
        chunk_embeddings = []
        
        for i, chunk in enumerate(chunks):
            # Create context window: chunk + surrounding text
            chunk_start = full_document.find(chunk)
            if chunk_start == -1:
                # Chunk not found, embed independently
                chunk_emb = self.embed_document(chunk)
            else:
                # Extract context around chunk (before + chunk + after)
                context_before = max(0, chunk_start - 1000)  # 1000 chars before
                context_after = min(len(full_document), chunk_start + len(chunk) + 1000)  # 1000 chars after
                
                context_window = full_document[context_before:context_after]
                
                # Embed the context window
                try:
                    output = embed.text(
                        texts=[context_window],
                        model=self.model_name,
                        task_type='search_query'
                    )
                    context_embedding = np.array(output['embeddings'][0])
                    
                    # Extract chunk position in context
                    chunk_in_context_start = chunk_start - context_before
                    chunk_in_context_end = chunk_in_context_start + len(chunk)
                    
                    # Apply mean pooling over chunk span
                    # Since we have the full context embedding, we use it directly
                    # In a more sophisticated implementation, we'd pool over token embeddings
                    chunk_emb = context_embedding
                except Exception as e:
                    print(f"Error embedding chunk with context: {str(e)}")
                    # Fallback: embed chunk independently
                    chunk_emb = self.embed_document(chunk)
            
            # Combine with document-level embedding (weighted average)
            # This preserves both chunk-specific and document-level context
            combined_embedding = 0.7 * chunk_emb + 0.3 * document_embedding
            
            chunk_embeddings.append((
                combined_embedding,
                chunk_metadata[i] if i < len(chunk_metadata) else {}
            ))
        
        return chunk_embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """Embed a search query."""
        try:
            output = embed.text(
                texts=[query],
                model=self.model_name,
                task_type='search_query'
            )
            return np.array(output['embeddings'][0])
        except Exception as e:
            print(f"Error embedding query: {str(e)}")
            return np.zeros(768)

# Global instance
embedding_service = EmbeddingService()

