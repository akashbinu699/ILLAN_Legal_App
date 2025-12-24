"""Retrieval service with hybrid search and re-ranking."""
from typing import List, Dict, Optional
from backend.services.embedding_service import embedding_service
from backend.services.vector_store import vector_store
from backend.config import settings
import cohere

class RetrievalService:
    """Service for hybrid search and re-ranking."""
    
    def __init__(self):
        self.cohere_client = None
        # Use RERANKER_API_KEY first, fall back to COHERE_API_KEY for backward compatibility
        api_key = settings.reranker_api_key or settings.cohere_api_key
        if api_key:
            try:
                self.cohere_client = cohere.Client(api_key=api_key)
            except:
                pass
    
    def hybrid_search(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Hybrid search combining vector search and keyword search (BM25).
        
        For now, we implement vector search. BM25 can be added later
        using a library like rank-bm25.
        """
        # Step 1: Embed the query
        query_embedding = embedding_service.embed_query(query)
        
        # Step 2: Vector search in ChromaDB
        vector_results = vector_store.search(
            query_embedding=query_embedding.tolist(),
            n_results=n_results * 2,  # Get more results for re-ranking
            filter_metadata=filter_metadata
        )
        
        # TODO: Add BM25 keyword search here
        # For now, we'll use vector search results
        
        return vector_results
    
    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """Re-rank chunks using Cohere or local reranker."""
        if not chunks:
            return []
        
        if self.cohere_client:
            # Use Cohere reranker
            try:
                documents = [chunk['document'] for chunk in chunks]
                rerank_response = self.cohere_client.rerank(
                    model='rerank-english-v3.0',
                    query=query,
                    documents=documents,
                    top_n=top_k
                )
                
                # Map reranked results back to chunks with metadata
                reranked_chunks = []
                for result in rerank_response.results:
                    original_chunk = chunks[result.index]
                    reranked_chunks.append({
                        **original_chunk,
                        'relevance_score': result.relevance_score
                    })
                
                return reranked_chunks
            except Exception as e:
                print(f"Error in Cohere reranking: {str(e)}")
                # Fallback to simple distance-based ranking
                return self._fallback_rerank(chunks, top_k)
        else:
            # Fallback: use distance-based ranking
            return self._fallback_rerank(chunks, top_k)
    
    def _fallback_rerank(self, chunks: List[Dict], top_k: int) -> List[Dict]:
        """Fallback reranking based on distance scores."""
        # Sort by distance (lower is better for cosine distance)
        sorted_chunks = sorted(
            chunks,
            key=lambda x: x.get('distance', 1.0) if x.get('distance') is not None else 1.0
        )
        
        return sorted_chunks[:top_k]
    
    def retrieve(
        self,
        query: str,
        n_results: int = 10,
        top_k: int = 3,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Complete retrieval pipeline: hybrid search + re-ranking.
        
        Returns top_k most relevant chunks with metadata.
        """
        # Step 1: Hybrid search
        search_results = self.hybrid_search(
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata
        )
        
        # Step 2: Re-rank
        reranked_results = self.rerank(
            query=query,
            chunks=search_results,
            top_k=top_k
        )
        
        return reranked_results

# Global instance
retrieval_service = RetrievalService()

