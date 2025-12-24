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
    
    # Format citations
    citations = []
    for citation_str in result.get('citations', []):
        # Parse citation string (format: "Doc-123, Page 2, Section: Title")
        # This is simplified - in production, use proper parsing
        citations.append({
            'document_id': 0,  # TODO: Extract from citation
            'page_number': 0,  # TODO: Extract from citation
            'section_title': None,
            'clause_number': None,
            'chunk_id': 0
        })
    
    return QueryResponse(
        response=result['answer'],
        citations=citations,
        retrieved_chunks=len(result.get('retrieved_chunks', [])),
        query_id=db_query.id
    )

