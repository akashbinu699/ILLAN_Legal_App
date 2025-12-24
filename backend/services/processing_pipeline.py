"""Main processing pipeline that orchestrates all steps."""
import base64
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Submission, Document, Chunk
from backend.services.document_processor import DocumentProcessor
from backend.services.cleaning_service import cleaning_service
from backend.services.embedding_service import embedding_service
from backend.services.vector_store import vector_store
from backend.services.duplicate_detection import DuplicateDetectionService
from typing import List, Dict
import asyncio

class ProcessingPipeline:
    """Orchestrates the complete processing pipeline."""
    
    @staticmethod
    async def process_submission(
        submission_id: int,
        files: List[Dict],
        db: AsyncSession
    ):
        """Process a submission through the complete pipeline."""
        # Get submission
        from sqlalchemy import select
        result = await db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        # Update status
        submission.status = "PROCESSING"
        await db.commit()
        
        try:
            # Process each file
            for file_data in files:
                # Decode base64 file
                file_bytes = base64.b64decode(file_data['base64'])
                
                # Step 3: Process document (PDF to text)
                processed = DocumentProcessor.process_document(
                    file_bytes,
                    file_data['name'],
                    file_data['mimeType']
                )
                
                # Step 4: Clean and standardize
                cleaned = cleaning_service.process_document(
                    processed['text'],
                    processed.get('tables', [])
                )
                
                # Create document record
                db_document = Document(
                    submission_id=submission_id,
                    filename=file_data['name'],
                    mime_type=file_data['mimeType'],
                    original_text=processed['text'],
                    cleaned_text=cleaned['cleaned_text'],
                    structured_data=cleaned['structured_data'],
                    page_count=processed.get('page_count', 1)
                )
                db.add(db_document)
                await db.flush()  # Get document ID
                
                # Step 5: Vectorization with Late Chunking
                # Chunk the document (simple chunking for now)
                chunks = ProcessingPipeline._chunk_document(cleaned['cleaned_text'])
                
                # Prepare chunk metadata
                chunk_metadata = [
                    {
                        'document_id': db_document.id,
                        'submission_id': submission_id,
                        'chunk_index': i,
                        'page_number': 1,  # TODO: Calculate actual page number
                        'section_title': '',
                        'clause_number': '',
                        'filename': file_data['name']
                    }
                    for i in range(len(chunks))
                ]
                
                # Generate embeddings with Late Chunking
                embeddings = embedding_service.embed_chunks_with_context(
                    full_document=cleaned['cleaned_text'],
                    chunks=chunks,
                    chunk_metadata=chunk_metadata
                )
                
                # Store in ChromaDB
                chunk_ids = vector_store.add_document_chunks(
                    chunks=chunks,
                    embeddings=[emb[0] for emb in embeddings],
                    metadata_list=[emb[1] for emb in embeddings]
                )
                
                # Create chunk records in database
                for i, (chunk, embedding_data, chunk_id) in enumerate(zip(chunks, embeddings, chunk_ids)):
                    db_chunk = Chunk(
                        document_id=db_document.id,
                        chunk_index=i,
                        content=chunk,
                        page_number=chunk_metadata[i]['page_number'],
                        section_title=chunk_metadata[i].get('section_title'),
                        clause_number=chunk_metadata[i].get('clause_number'),
                        embedding_id=chunk_id
                    )
                    db.add(db_chunk)
            
            # Update submission status
            submission.status = "REVIEWED"
            await db.commit()
            
        except Exception as e:
            print(f"Error processing submission {submission_id}: {str(e)}")
            submission.status = "NEW"  # Reset on error
            await db.commit()
            raise
    
    @staticmethod
    def _chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Chunk document into smaller pieces."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap  # Overlap for context
        
        return chunks

# Global instance
processing_pipeline = ProcessingPipeline()

