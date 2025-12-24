"""API routes for the backend."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio
from backend.database.db import get_db
from backend.api.schemas import (
    SubmissionCreate,
    SubmissionResponse,
    QueryRequest,
    QueryResponse,
    CaseResponse
)
from backend.database.models import Submission
from datetime import datetime

router = APIRouter()

@router.post("/submit", response_model=SubmissionResponse)
async def submit_case(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Receive form submission from frontend."""
    try:
        # Generate case ID
        year = datetime.now().year
        # Get count of existing cases for this year
        from sqlalchemy import select, func
        result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.case_id.like(f"CAS-{year}-%")
            )
        )
        count = result.scalar() or 0
        sequence = str(count + 1).zfill(3)
        case_id = f"CAS-{year}-{sequence}"
        
        # Create submission record
        db_submission = Submission(
            case_id=case_id,
            email=submission.email,
            phone=submission.phone,
            description=submission.description,
            submitted_at=datetime.utcnow(),
            status="NEW",
            stage="RAPO"
        )
        
        db.add(db_submission)
        await db.commit()
        await db.refresh(db_submission)
        
        # Trigger document processing pipeline (async background task)
        # Create a new session for the background task since the request session will close
        from backend.services.processing_pipeline import processing_pipeline
        from backend.database.db import AsyncSessionLocal
        
        async def process_in_background():
            async with AsyncSessionLocal() as bg_db:
                try:
                    await processing_pipeline.process_submission(
                        db_submission.id,
                        [{"name": f.name, "mimeType": f.mimeType, "base64": f.base64} for f in submission.files],
                        bg_db
                    )
                except Exception as e:
                    print(f"Background processing error: {e}")
                    import traceback
                    traceback.print_exc()
        
        asyncio.create_task(process_in_background())
        
        return SubmissionResponse.model_validate(db_submission)
    except Exception as e:
        print(f"Error in submit_case: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing submission: {str(e)}")

@router.get("/cases", response_model=List[CaseResponse])
async def get_cases(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all cases for lawyer dashboard."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.documents))
        .order_by(Submission.submitted_at.desc())
        .offset(skip)
        .limit(limit)
    )
    submissions = result.scalars().all()
    
    # Convert to response format
    cases = []
    for sub in submissions:
        # TODO: Add prestations, drafts when available
        case = CaseResponse(
            id=sub.id,
            case_id=sub.case_id,
            email=sub.email,
            phone=sub.phone,
            description=sub.description,
            submitted_at=sub.submitted_at,
            status=sub.status,
            stage=sub.stage,
            prestations=[],
            generatedEmailDraft=None,
            generatedAppealDraft=None
        )
        cases.append(case)
    
    return cases

@router.get("/case/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific case by case_id."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Submission).where(Submission.case_id == case_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # TODO: Add prestations, drafts when available
    return CaseResponse(
        id=submission.id,
        case_id=submission.case_id,
        email=submission.email,
        phone=submission.phone,
        description=submission.description,
        submitted_at=submission.submitted_at,
        status=submission.status,
        stage=submission.stage,
        prestations=[],
        generatedEmailDraft=None,
        generatedAppealDraft=None
    )

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    query: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """RAG query endpoint for Ilan."""
    try:
        from backend.services.rag_pipeline import rag_pipeline
        from backend.database.models import Query as QueryModel
        
        # Run RAG pipeline
        result = rag_pipeline.run(query.query)
        
        # Save query to database
        db_query = QueryModel(
            query_text=query.query,
            response_text=result['answer'],
            citations=result.get('citations', []),
            retrieved_chunk_ids=[chunk.get('id') for chunk in result.get('retrieved_chunks', [])]
        )
        db.add(db_query)
        await db.commit()
        await db.refresh(db_query)
        
        # Format citations from retrieved chunks
        # The LLM response contains citations in format [Document X, Page Y]
        # We need to map these to actual chunk metadata
        retrieved_chunks = result.get('retrieved_chunks', [])
        citations = []
        
        # Extract citation patterns from the response
        import re
        citation_patterns = re.findall(r'\[Document\s+(\d+),\s*Page\s+(\d+)(?:,\s*Section:\s*([^\]]+))?\]', result['answer'])
        
        # Create a map of document_id -> chunks for quick lookup
        chunk_map = {}
        for chunk in retrieved_chunks:
            doc_id = chunk.get('metadata', {}).get('document_id', 0)
            if doc_id not in chunk_map:
                chunk_map[doc_id] = []
            chunk_map[doc_id].append(chunk)
        
        # Process each citation pattern found in the response
        seen_citations = set()
        for doc_id_str, page_str, section in citation_patterns:
            try:
                doc_id = int(doc_id_str)
                page_num = int(page_str)
                
                # Create unique key to avoid duplicates
                citation_key = (doc_id, page_num)
                if citation_key in seen_citations:
                    continue
                seen_citations.add(citation_key)
                
                # Find matching chunk
                matching_chunk = None
                if doc_id in chunk_map:
                    # Find chunk with matching page number
                    for chunk in chunk_map[doc_id]:
                        chunk_page = chunk.get('metadata', {}).get('page_number', 0)
                        if chunk_page == page_num or chunk_page == 0:  # Allow 0 as fallback
                            matching_chunk = chunk
                            break
                
                if matching_chunk:
                    chunk_id = matching_chunk.get('id', 0)
                    # Handle UUID strings - convert to integer hash for schema compatibility
                    if isinstance(chunk_id, str):
                        # Use hash of UUID string as integer ID
                        chunk_id = abs(hash(chunk_id)) % (10**9)  # Keep it within reasonable int range
                    
                    citations.append({
                        'document_id': doc_id,
                        'page_number': page_num,
                        'section_title': section.strip() if section else matching_chunk.get('metadata', {}).get('section_title'),
                        'clause_number': matching_chunk.get('metadata', {}).get('clause_number'),
                        'chunk_id': chunk_id
                    })
                else:
                    # Fallback: create citation from pattern even if chunk not found
                    citations.append({
                        'document_id': doc_id,
                        'page_number': page_num,
                        'section_title': section.strip() if section else None,
                        'clause_number': None,
                        'chunk_id': 0
                    })
            except (ValueError, KeyError):
                # Skip invalid citation patterns
                continue
        
        # If no citations found from patterns, use retrieved chunks as citations
        if not citations and retrieved_chunks:
            for chunk in retrieved_chunks[:5]:  # Limit to first 5
                metadata = chunk.get('metadata', {})
                chunk_id = chunk.get('id', 0)
                # Handle UUID strings - convert to integer hash for schema compatibility
                if isinstance(chunk_id, str):
                    chunk_id = abs(hash(chunk_id)) % (10**9)  # Keep it within reasonable int range
                
                citations.append({
                    'document_id': metadata.get('document_id', 0),
                    'page_number': metadata.get('page_number', 0),
                    'section_title': metadata.get('section_title'),
                    'clause_number': metadata.get('clause_number'),
                    'chunk_id': chunk_id
                })
        
        return QueryResponse(
            response=result['answer'],
            citations=citations,
            retrieved_chunks=len(result.get('retrieved_chunks', [])),
            query_id=db_query.id
        )
    except Exception as e:
        print(f"Error in query_rag: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

