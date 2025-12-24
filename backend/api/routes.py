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
    CaseResponse,
    CaseUpdate,
    QueryHistoryResponse,
    GenerateDraftRequest,
    GenerateDraftResponse,
    StageDetectionRequest,
    StageDetectionResponse,
    EmailGroupResponse
)
from backend.database.models import Submission, Query as QueryModel
from datetime import datetime

router = APIRouter()

@router.post("/submit", response_model=SubmissionResponse)
async def submit_case(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Receive form submission from frontend."""
    try:
        # Generate case ID with timestamp format: CAS_DD-MM-YY_HH:MM:SS
        now = datetime.now()
        case_id = f"CAS_{now.strftime('%d-%m-%y_%H:%M:%S')}"
        
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
        # This runs in the background and doesn't block the response
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
                    print(f"Background processing error for submission {db_submission.id}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Update status to indicate processing failed
                    try:
                        result = await bg_db.execute(
                            select(Submission).where(Submission.id == db_submission.id)
                        )
                        sub = result.scalar_one_or_none()
                        if sub:
                            sub.status = "NEW"  # Reset status on error
                            await bg_db.commit()
                    except Exception as update_error:
                        print(f"Failed to update status after processing error: {update_error}")
        
        # Fire and forget - don't await, let it run in background
        asyncio.create_task(process_in_background())
        
        return SubmissionResponse.model_validate(db_submission)
    except Exception as e:
        print(f"Error in submit_case: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing submission: {str(e)}")

@router.get("/cases", response_model=List[EmailGroupResponse])
async def get_cases(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all cases grouped by email address for lawyer dashboard."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from collections import defaultdict
    
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.documents))
        .order_by(Submission.submitted_at.desc())
        .offset(skip)
        .limit(limit)
    )
    submissions = result.scalars().all()
    
    # Group submissions by email
    email_groups = defaultdict(list)
    for sub in submissions:
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
            generatedEmailDraft=sub.generated_email_draft,
            generatedAppealDraft=sub.generated_appeal_draft,
            emailPrompt=sub.email_prompt,
            appealPrompt=sub.appeal_prompt
        )
        email_groups[sub.email].append(case)
    
    # Convert to response format - cases within each group are already ordered by submitted_at DESC
    # Sort email groups by most recent case submission time
    email_group_list = []
    for email, cases in email_groups.items():
        # Cases are already in descending order (newest first) from the query
        # But we'll ensure they're sorted by submitted_at DESC within the group
        cases_sorted = sorted(cases, key=lambda c: c.submitted_at, reverse=True)
        email_group_list.append(EmailGroupResponse(
            email=email,
            cases=cases_sorted
        ))
    
    # Sort email groups by the most recent case submission time (newest first)
    email_group_list.sort(key=lambda g: g.cases[0].submitted_at if g.cases else datetime.min, reverse=True)
    
    return email_group_list

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
        generatedEmailDraft=submission.generated_email_draft,
        generatedAppealDraft=submission.generated_appeal_draft,
        emailPrompt=submission.email_prompt,
        appealPrompt=submission.appeal_prompt
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
        from sqlalchemy import select
        
        # Lookup submission_id from case_id BEFORE running pipeline (for filtering)
        submission_id = None
        filter_metadata = None
        if query.case_id:
            sub_result = await db.execute(
                select(Submission).where(Submission.case_id == query.case_id)
            )
            submission = sub_result.scalar_one_or_none()
            if submission:
                submission_id = submission.id
                # Create filter metadata to only search documents from this case
                filter_metadata = {'submission_id': str(submission_id)}
        
        # Run RAG pipeline with optional filter
        result = rag_pipeline.run(query.query, filter_metadata=filter_metadata)
        
        # Save query to database
        db_query = QueryModel(
            submission_id=submission_id,
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

@router.patch("/case/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    update: CaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update case fields (drafts, prompts, stage, status)."""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(Submission).where(Submission.case_id == case_id)
        )
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Update fields if provided
        if update.generatedEmailDraft is not None:
            submission.generated_email_draft = update.generatedEmailDraft
        if update.generatedAppealDraft is not None:
            submission.generated_appeal_draft = update.generatedAppealDraft
        if update.emailPrompt is not None:
            submission.email_prompt = update.emailPrompt
        if update.appealPrompt is not None:
            submission.appeal_prompt = update.appealPrompt
        if update.stage is not None:
            submission.stage = update.stage
        if update.status is not None:
            submission.status = update.status
        
        await db.commit()
        await db.refresh(submission)
        
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
            generatedEmailDraft=submission.generated_email_draft,
            generatedAppealDraft=submission.generated_appeal_draft,
            emailPrompt=submission.email_prompt,
            appealPrompt=submission.appeal_prompt
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_case: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating case: {str(e)}")

@router.post("/case/{case_id}/generate-drafts", response_model=CaseResponse)
async def generate_drafts(
    case_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate email and appeal drafts for a case if missing."""
    try:
        from sqlalchemy import select
        from backend.services.llm_service import llm_service
        
        result = await db.execute(
            select(Submission).where(Submission.case_id == case_id)
        )
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Generate email draft if missing
        if not submission.generated_email_draft:
            email_prompt = f"""Generate a professional email draft for a legal case.

Case ID: {submission.case_id}
Client Email: {submission.email}
Client Phone: {submission.phone}
Case Description: {submission.description}
Stage: {submission.stage}

Generate a professional email draft that can be sent to the client."""
            
            try:
                email_draft = await llm_service.generate(email_prompt)
                submission.generated_email_draft = email_draft
                submission.email_prompt = email_prompt
            except Exception as e:
                print(f"Error generating email draft: {e}")
                # Continue even if generation fails
        
        # Generate appeal draft if missing
        if not submission.generated_appeal_draft:
            appeal_prompt = f"""Generate a professional appeal draft for a legal case.

Case ID: {submission.case_id}
Client Email: {submission.email}
Client Phone: {submission.phone}
Case Description: {submission.description}
Stage: {submission.stage}

Generate a professional appeal draft that can be used for legal proceedings."""
            
            try:
                appeal_draft = await llm_service.generate(appeal_prompt)
                submission.generated_appeal_draft = appeal_draft
                submission.appeal_prompt = appeal_prompt
            except Exception as e:
                print(f"Error generating appeal draft: {e}")
                # Continue even if generation fails
        
        await db.commit()
        await db.refresh(submission)
        
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
            generatedEmailDraft=submission.generated_email_draft,
            generatedAppealDraft=submission.generated_appeal_draft,
            emailPrompt=submission.email_prompt,
            appealPrompt=submission.appeal_prompt
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_drafts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating drafts: {str(e)}")

@router.post("/case/{case_id}/generate-draft", response_model=GenerateDraftResponse)
async def generate_single_draft(
    case_id: str,
    request: GenerateDraftRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a single draft (email or appeal) with a custom prompt."""
    try:
        from sqlalchemy import select
        from backend.services.llm_service import llm_service
        
        result = await db.execute(
            select(Submission).where(Submission.case_id == case_id)
        )
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Generate draft using the provided prompt
        try:
            draft = await llm_service.generate(request.prompt)
            
            # Update the submission with the generated draft and prompt
            if request.draft_type == 'email':
                submission.generated_email_draft = draft
                submission.email_prompt = request.prompt
            elif request.draft_type == 'appeal':
                submission.generated_appeal_draft = draft
                submission.appeal_prompt = request.prompt
            
            await db.commit()
            
            return GenerateDraftResponse(
                draft=draft,
                prompt=request.prompt
            )
        except Exception as e:
            print(f"Error generating draft: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error generating draft: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_single_draft: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating draft: {str(e)}")

@router.post("/detect-stage", response_model=StageDetectionResponse)
async def detect_stage(
    request: StageDetectionRequest
):
    """Detect legal stage and prestations from case description and files."""
    try:
        from backend.services.llm_service import llm_service
        import json
        
        # Knowledge base (simplified - in production, load from file)
        KNOWLEDGE_BASE = """THEME,RENSEIGNEMENTS
"Recours dont traite le cabinet (✅), et recours dont il ne traite pas (❌) (Généralités)","Notre cabinet pratique en droit public et ne connait que des recours et contentieux administratifs. Nous ne traitons pas des affaires qui relèvent du tribunal judiciaire. Par ailleurs, nous ne traitons pas non plus des prestations relatives au handicap, ou celles ne relevant pas du tribunal administratif (AAH, AEEH, AJPP, AJPA, AVPF, etc.)."
"Aides personnelles au logement (APLs) et Prime de déménagement ✅","Pour contester la décision de la caisse d'Allocations familiales (Caf) : Recours amiable puis contentieux devant tribunal administratif."
"Revenu de solidarité active (RSA) ✅","Pour contester la décision : Recours amiable puis contentieux devant tribunal administratif."
"Prime d'activité ✅","Pour contester la décision : Recours amiable puis contentieux devant tribunal administratif."
"""
        
        # Build prompt for stage detection
        prompt = f"""CONTEXTE:
Tu es avocat spécialisé en droit administratif (CAF). 
Tu rédiges pour le compte de Maître Ilan BRUN-VARGAS.

BASE DE CONNAISSANCES DU CABINET (Ce que nous traitons ou non):
{KNOWLEDGE_BASE}

DESCRIPTION DU CAS PAR LE CLIENT:
"{request.description}"

TÂCHE:
Analysez la description pour :
1. Identifier l'étape précise de la procédure (stage).
2. Identifier TOUTES les prestations concernées (RSA, APL, AAH, etc.). Il peut y en avoir plusieurs.
3. Pour chaque prestation, déterminer si le cabinet traite ce type de recours selon la Base de Connaissances (isAccepted).

RÈGLES DE CLASSIFICATION (STAGE):
1. CONTROL : Lettre de fin de contrôle, Procédure contradictoire, invitation à observations. Pas d'indu formel.
2. RAPO : Notification d'indu, révision de droits, délai de 2 mois ouvert pour CRA/Président CD.
3. LITIGATION : RAPO rejeté (explicite ou implicite), saisine Tribunal Administratif.

RÈGLES D'ACCEPTATION (isAccepted):
- Regardez la colonne "Recours dont traite le cabinet" dans la Base de Connaissances.
- ✅ = Accepté (RSA, Prime d'activité, APL, etc.).
- ❌ = Refusé (Handicap, AAH, AEEH, Tribunal Judiciaire, etc.).

Retournez uniquement le JSON suivant :
{{ 
  "stage": "CONTROL" | "RAPO" | "LITIGATION",
  "prestations": [
    {{ "name": "Nom de la prestation", "isAccepted": true | false }}
  ]
}}"""
        
        # Generate response using LLM (Gemini 3 → OpenAI → Groq)
        response_text = await llm_service.generate(prompt, max_tokens=1000, temperature=0.3)
        
        # Parse JSON response
        try:
            # Extract JSON from response (might have markdown code blocks)
            import re
            json_match = re.search(r'\{[^{}]*"stage"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            result = json.loads(json_str)
            
            return StageDetectionResponse(
                stage=result.get("stage", "RAPO"),
                prestations=[
                    {"name": p.get("name", "Non identifiée"), "isAccepted": p.get("isAccepted", True)}
                    for p in result.get("prestations", [])
                ]
            )
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response_text}")
            # Return default
            return StageDetectionResponse(
                stage="RAPO",
                prestations=[{"name": "Non identifiée", "isAccepted": True}]
            )
            
    except Exception as e:
        print(f"Error in detect_stage: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error detecting stage: {str(e)}")

@router.get("/case/{case_id}/queries", response_model=List[QueryHistoryResponse])
async def get_case_queries(
    case_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get query history for a specific case."""
    try:
        from sqlalchemy import select
        
        # First get the submission
        result = await db.execute(
            select(Submission).where(Submission.case_id == case_id)
        )
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Get all queries for this submission
        query_result = await db.execute(
            select(QueryModel)
            .where(QueryModel.submission_id == submission.id)
            .order_by(QueryModel.created_at.desc())
        )
        queries = query_result.scalars().all()
        
        # Convert to response format
        query_responses = []
        for q in queries:
            # Parse citations from JSON
            citations = []
            if q.citations:
                for cit in q.citations if isinstance(q.citations, list) else []:
                    citations.append({
                        'document_id': cit.get('document_id', 0),
                        'page_number': cit.get('page_number', 0),
                        'section_title': cit.get('section_title'),
                        'clause_number': cit.get('clause_number'),
                        'chunk_id': cit.get('chunk_id', 0)
                    })
            
            query_responses.append(QueryHistoryResponse(
                id=q.id,
                query_text=q.query_text,
                response_text=q.response_text,
                citations=citations,
                retrieved_chunk_ids=q.retrieved_chunk_ids,
                created_at=q.created_at
            ))
        
        return query_responses
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_case_queries: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving queries: {str(e)}")

