"""Main processing pipeline that orchestrates all steps."""
import base64
from backend.services.document_processor import DocumentProcessor
from backend.services.cleaning_service import cleaning_service
from backend.services.embedding_service import embedding_service
from backend.services.vector_store import vector_store
from typing import List, Dict
import asyncio
from bson import ObjectId

class ProcessingPipeline:
    """Orchestrates the complete processing pipeline."""
    
    @staticmethod
    async def process_submission(
        submission_id: str,
        files: List[Dict],
        db
    ):
        """Process a submission through the complete pipeline."""
        # Get submission
        try:
            submission = await db.submissions.find_one({"_id": ObjectId(submission_id)})
            
            if not submission:
                print(f"Submission {submission_id} not found in background task")
                return
            
            # Update status
            await db.submissions.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {"status": "PROCESSING"}}
            )
            
            # Process each file (typically just one per split submission)
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
                
                # Update submission's embedded document with results
                doc_update = {
                    "document.original_text": processed['text'],
                    "document.cleaned_text": cleaned['cleaned_text'],
                    "document.structured_data": cleaned['structured_data'],
                    "document.page_count": processed.get('page_count', 1),
                    "document.processed_at": asyncio.get_event_loop().time() # Use simple timestamp or isoformat
                }
                
                # Step 5: Vectorization with Late Chunking
                # Chunk the document
                chunks_text = ProcessingPipeline._chunk_document(cleaned['cleaned_text'])
                
                # Prepare chunk metadata for ChromaDB
                # Use string ID for document_id since it's embedded
                doc_id_str = submission_id 
                
                chunk_metadata = [
                    {
                        'document_id': doc_id_str, # Using submission ID as doc ID proxy since 1:1
                        'submission_id': submission_id,
                        'chunk_index': i,
                        'page_number': 1,
                        'section_title': '',
                        'clause_number': '',
                        'filename': file_data['name']
                    }
                    for i in range(len(chunks_text))
                ]
                
                # Generate embeddings
                embeddings = embedding_service.embed_chunks_with_context(
                    full_document=cleaned['cleaned_text'],
                    chunks=chunks_text,
                    chunk_metadata=chunk_metadata
                )
                
                # Store in ChromaDB
                chunk_ids = vector_store.add_document_chunks(
                    chunks=chunks_text,
                    embeddings=[emb[0] for emb in embeddings],
                    metadata_list=[emb[1] for emb in embeddings]
                )
                
                # Create chunk objects for Mongo
                mongo_chunks = []
                for i, (chunk_txt, embedding_data, chunk_id) in enumerate(zip(chunks_text, embeddings, chunk_ids)):
                    mongo_chunks.append({
                        "chunk_index": i,
                        "content": chunk_txt,
                        "page_number": chunk_metadata[i]['page_number'],
                        "section_title": chunk_metadata[i].get('section_title'),
                        "clause_number": chunk_metadata[i].get('clause_number'),
                        "embedding_id": chunk_id
                    })
                
                doc_update["document.chunks"] = mongo_chunks
                
                # Perform the update
                await db.submissions.update_one(
                    {"_id": ObjectId(submission_id)},
                    {"$set": doc_update}
                )
            
            # Final status update
            await db.submissions.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {"status": "REVIEWED"}}
            )
            
        except Exception as e:
            print(f"Error processing submission {submission_id}: {str(e)}")
            await db.submissions.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {"status": "NEW"}}
            )
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def _chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Chunk document into smaller pieces."""
        chunks = []
        if not text:
            return []
            
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap  # Overlap for context
        
        return chunks

# Global instance
processing_pipeline = ProcessingPipeline()
