"""ChromaDB vector store service."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from backend.config import settings
import uuid

class VectorStore:
    """Service for managing vector storage in ChromaDB."""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name="legal_documents",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
    
    def add_document_chunks(
        self,
        chunks: List[str],
        embeddings: List,
        metadata_list: List[Dict]
    ) -> List[str]:
        """Add document chunks to ChromaDB with embeddings and metadata."""
        ids = []
        
        for i, (chunk, embedding, metadata) in enumerate(zip(chunks, embeddings, metadata_list)):
            # Generate unique ID
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            
            # Prepare metadata (ChromaDB requires string values)
            chroma_metadata = {
                'document_id': str(metadata.get('document_id', '')),
                'submission_id': str(metadata.get('submission_id', '')),
                'chunk_index': str(metadata.get('chunk_index', i)),
                'page_number': str(metadata.get('page_number', '')),
                'section_title': metadata.get('section_title', '') or '',
                'clause_number': metadata.get('clause_number', '') or '',
                'filename': metadata.get('filename', '') or ''
            }
            
            # Add to collection
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding.tolist() if hasattr(embedding, 'tolist') else embedding],
                documents=[chunk],
                metadatas=[chroma_metadata]
            )
        
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar chunks."""
        where_clause = None
        if filter_metadata:
            where_clause = filter_metadata
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_by_ids(self, ids: List[str]) -> List[Dict]:
        """Retrieve chunks by their IDs."""
        results = self.collection.get(ids=ids)
        
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'])):
                formatted_results.append({
                    'id': results['ids'][i],
                    'document': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
        
        return formatted_results
    
    def delete_by_document_id(self, document_id: int):
        """Delete all chunks for a specific document."""
        # Get all chunks for this document
        results = self.collection.get(
            where={'document_id': str(document_id)}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
    
    def delete_by_submission_id(self, submission_id: int):
        """Delete all chunks for a specific submission."""
        results = self.collection.get(
            where={'submission_id': str(submission_id)}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])

# Global instance
vector_store = VectorStore()

