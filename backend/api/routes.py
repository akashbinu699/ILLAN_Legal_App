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
from sqlalchemy import select, func

router = APIRouter()

def format_date_ddmmmyy(dt: datetime) -> str:
    """Format datetime as DDMMMYY (e.g., 01JAN25, 21FEB25)."""
    month_names = {
        1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
        7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
    }
    day = dt.strftime('%d')
    month = month_names[dt.month]
    year = dt.strftime('%y')
    return f"{day}{month}{year}"

@router.post("/submit", response_model=SubmissionResponse)
async def submit_case(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Receive form submission from frontend."""
    try:
        # Generate case ID with timestamp format: CAS_DD-MM-YY_HH:MM:SS
        # This will be shared by all split submissions from this form
        now = datetime.now()
        case_id = f"CAS_{now.strftime('%d-%m-%y_%H:%M:%S')}"
        submitted_at = datetime.utcnow()
        
        # Assign CAS number to email
        # Check if email already has a CAS number
        existing_submission = await db.execute(
            select(Submission).where(Submission.email == submission.email).limit(1)
        )
        existing = existing_submission.scalar_one_or_none()
        
        if existing and existing.cas_number is not None:
            # Reuse existing CAS number for this email
            cas_number = existing.cas_number
        else:
            # Assign new CAS number - find max and increment
            max_result = await db.execute(
                select(func.max(Submission.cas_number))
            )
            max_cas = max_result.scalar()
            cas_number = (max_cas + 1) if max_cas is not None else 1
        
        # Create one Submission record per document (split by document)
        # All share the same metadata: case_id, cas_number, email, phone, description, submitted_at
        from backend.database.models import Document
        created_submissions = []
        
        for file_data in submission.files:
            # Create one Submission per document
            db_submission = Submission(
                case_id=case_id,  # Same case_id for all split submissions
                cas_number=cas_number,  # Same CAS number
                email=submission.email,
                phone=submission.phone,
                description=submission.description,
                submitted_at=submitted_at,  # Same timestamp
                status="NEW",
                stage="RAPO"
            )
            db.add(db_submission)
            await db.flush()  # Get the submission ID
            
            # Create one Document record linked to this Submission
            db_document = Document(
                submission_id=db_submission.id,
                filename=file_data.name,
                mime_type=file_data.mimeType,
                original_text="",  # Will be filled during processing
                cleaned_text="",  # Will be filled during processing
                structured_data={},  # Will be filled during processing
                page_count=0  # Will be filled during processing
            )
            db.add(db_document)
            created_submissions.append(db_submission)
        
        await db.commit()
        
        # Refresh all created submissions
        for sub in created_submissions:
            await db.refresh(sub)
        
        # Use the first submission for response (they all share the same metadata)
        db_submission = created_submissions[0]
        
        # Send email notification (async, don't block response)
        # Send one email for the entire submission (all split submissions share the same case_id)
        async def send_notification_email():
            try:
                from backend.services.gmail_service import gmail_service
                from backend.config import settings
                from backend.database.db import AsyncSessionLocal
                
                print(f"[EMAIL] Starting email notification process...")
                print(f"[EMAIL] NOTIFICATION_EMAIL from settings: {settings.notification_email}")
                
                if not settings.notification_email:
                    print("[EMAIL] ERROR: NOTIFICATION_EMAIL not configured, skipping email send")
                    return
                
                print(f"[EMAIL] Notification email configured: {settings.notification_email}")
                
                # Get all split submissions with the same case_id to list all documents
                async with AsyncSessionLocal() as email_db:
                    # Get all submissions with the same case_id (all split submissions from this form)
                    result = await email_db.execute(
                        select(Submission).where(Submission.case_id == case_id).order_by(Submission.id.asc())
                    )
                    all_split_subs = result.scalars().all()
                    
                    if not all_split_subs:
                        print(f"[EMAIL] ERROR: Could not find submissions with case_id {case_id}")
                        return
                    
                    # Use the first submission for metadata (they all share the same)
                    first_submission = all_split_subs[0]
                    
                    # Get all document filenames from all split submissions
                    from sqlalchemy.orm import selectinload
                    all_filenames = []
                    for sub in all_split_subs:
                        result = await email_db.execute(
                            select(Submission).options(selectinload(Submission.documents)).where(Submission.id == sub.id)
                        )
                        sub_with_docs = result.scalar_one()
                        if sub_with_docs.documents:
                            all_filenames.append(sub_with_docs.documents[0].filename)
                    
                    # Get all submissions for this email to calculate form number
                    all_subs_for_email = await email_db.execute(
                        select(Submission).where(Submission.email == submission.email).order_by(Submission.submitted_at.asc())
                    )
                    all_subs = all_subs_for_email.scalars().all()
                    
                    # Find the first submission from this case_id to determine form number
                    first_submission_idx = None
                    for idx, sub in enumerate(all_subs, start=1):
                        if sub.case_id == case_id:
                            first_submission_idx = idx
                            break
                    
                    # Use the committed cas_number from the database (ensures consistency)
                    committed_cas_number = first_submission.cas_number
                    if committed_cas_number is None:
                        print(f"[EMAIL] WARNING: cas_number is None, using calculated value")
                        committed_cas_number = cas_number
                    
                    # Format date as DDMMMYY
                    date_formatted = format_date_ddmmmyy(first_submission.submitted_at)
                    
                    # Format display name with all filenames (for email subject/body)
                    filename_str = "_".join(all_filenames) if all_filenames else ""
                    if filename_str:
                        display_name = f"CASE{committed_cas_number}_{submission.email}_{filename_str}_{date_formatted}"
                    else:
                        display_name = f"CASE{committed_cas_number}_{submission.email}_{date_formatted}"
                
                # Format email subject - use committed cas_number
                cas_display_name = f"CAS-{committed_cas_number}_{submission.email}"
                subject = f"New Case Submission: {cas_display_name} - {display_name}"
                
                # Format email body - just the values, one per line, no labels
                body = f"""{display_name}
{submission.email}
{submission.phone}
{submission.description}
"""
                
                # Send email with all attachments from original submission
                attachments = [
                    {
                        'name': f.name,
                        'mimeType': f.mimeType,
                        'base64': f.base64
                    }
                    for f in submission.files
                ]
                
                print(f"[EMAIL] Attempting to send email to {settings.notification_email}")
                print(f"[EMAIL] Subject: {subject}")
                print(f"[EMAIL] Number of attachments: {len(attachments)}")
                
                success = gmail_service.send_email_with_attachments(
                    to_email=settings.notification_email,
                    subject=subject,
                    body=body,
                    attachments=attachments
                )
                
                if success:
                    print(f"[EMAIL] SUCCESS: Notification email sent successfully to {settings.notification_email}")
                else:
                    print(f"[EMAIL] ERROR: Failed to send notification email to {settings.notification_email}")
                    
            except Exception as e:
                print(f"[EMAIL] EXCEPTION: Error sending notification email: {e}")
                import traceback
                traceback.print_exc()
        
        # Fire and forget - send email in background
        asyncio.create_task(send_notification_email())
        
        # Trigger document processing pipeline (async background task)
        # Process each split submission separately (each has one document)
        # Create a new session for the background task since the request session will close
        # This runs in the background and doesn't block the response
        from backend.services.processing_pipeline import processing_pipeline
        from backend.database.db import AsyncSessionLocal
        
        async def process_in_background():
            async with AsyncSessionLocal() as bg_db:
                try:
                    # Process each split submission (one document each)
                    for idx, sub in enumerate(created_submissions):
                        try:
                            # Get the corresponding file data
                            file_data = submission.files[idx]
                            await processing_pipeline.process_submission(
                                sub.id,
                                [{"name": file_data.name, "mimeType": file_data.mimeType, "base64": file_data.base64}],
                                bg_db
                            )
                        except Exception as sub_error:
                            print(f"Background processing error for submission {sub.id}: {sub_error}")
                            import traceback
                            traceback.print_exc()
                            # Update status to indicate processing failed for this submission
                            try:
                                result = await bg_db.execute(
                                    select(Submission).where(Submission.id == sub.id)
                                )
                                failed_sub = result.scalar_one_or_none()
                                if failed_sub:
                                    failed_sub.status = "NEW"  # Reset status on error
                                    await bg_db.commit()
                            except Exception as update_error:
                                print(f"Failed to update status after processing error: {update_error}")
                except Exception as e:
                    print(f"Background processing error: {e}")
                    import traceback
                    traceback.print_exc()
        
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
        email_groups[sub.email].append(sub)
    
    # Convert to response format with form numbering and display names
    email_group_list = []
    for email, subs in email_groups.items():
        # Sort by submitted_at ASC (oldest first), then by case_id to group split submissions
        subs_sorted_asc = sorted(subs, key=lambda s: (s.submitted_at, s.case_id, s.id))
        
        # Get CAS number from first submission (all should have same CAS number for same email)
        cas_number = subs_sorted_asc[0].cas_number if subs_sorted_asc[0].cas_number is not None else 0
        
        # Group submissions by case_id to handle form numbering for split submissions
        # Submissions with the same case_id are from the same original form submission
        case_id_groups = defaultdict(list)
        for sub in subs_sorted_asc:
            case_id_groups[sub.case_id].append(sub)
        
        # Create cases with form numbers and display names
        cases_with_numbers = []
        form_counter = 1
        
        # Process each case_id group (original form submission) in chronological order
        # Sort by the earliest submitted_at in each group
        sorted_case_groups = sorted(
            case_id_groups.items(),
            key=lambda x: min(s.submitted_at for s in x[1]) if x[1] else datetime.min
        )
        
        for case_id, case_subs in sorted_case_groups:
            # Sort submissions within the same case_id by ID to maintain order
            case_subs_sorted = sorted(case_subs, key=lambda s: s.id)
            
            # Each submission in this group gets a sequential form number
            for sub in case_subs_sorted:
                # Format date as DDMMMYY
                date_formatted = format_date_ddmmmyy(sub.submitted_at)
                
                # Each submission now has only one document (1:1 relationship)
                # Get the single document filename
                filename = ""
                if sub.documents and len(sub.documents) > 0:
                    filename = sub.documents[0].filename
                
                # Format: CASE{number}_{email}_{single_filename}_{date}
                if filename:
                    display_name = f"CASE{cas_number}_{email}_{filename}_{date_formatted}"
                else:
                    display_name = f"CASE{cas_number}_{email}_{date_formatted}"
                
                case = CaseResponse(
                    id=sub.id,
                    case_id=sub.case_id,
                    cas_number=cas_number,
                    email=sub.email,
                    phone=sub.phone,
                    description=sub.description,
                    submitted_at=sub.submitted_at,
                    status=sub.status,
                    stage=sub.stage,
                    prestations=[],
                    display_name=display_name,
                    generatedEmailDraft=sub.generated_email_draft,
                    generatedAppealDraft=sub.generated_appeal_draft,
                    emailPrompt=sub.email_prompt,
                    appealPrompt=sub.appeal_prompt
                )
                cases_with_numbers.append(case)
                form_counter += 1
        
        # Reverse sort for display (newest first)
        cases_sorted_desc = sorted(cases_with_numbers, key=lambda c: c.submitted_at, reverse=True)
        
        # Email group header shows only email (no CAS prefix)
        cas_display_name = email
        
        email_group_list.append(EmailGroupResponse(
            email=email,
            cas_number=cas_number,
            cas_display_name=cas_display_name,
            cases=cases_sorted_desc
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
    
    # Calculate display name for this case
    # Load documents for this submission
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Submission).options(selectinload(Submission.documents)).where(Submission.id == submission.id)
    )
    submission = result.scalar_one()
    
    # Format date as DDMMMYY
    date_formatted = format_date_ddmmmyy(submission.submitted_at)
    
    # Each submission now has only one document (1:1 relationship)
    # Get the single document filename
    filename = ""
    if submission.documents and len(submission.documents) > 0:
        filename = submission.documents[0].filename
    
    # Get CAS number
    cas_number = submission.cas_number if submission.cas_number is not None else 0
    
    # Format: CASE{number}_{email}_{single_filename}_{date}
    if filename:
        display_name = f"CASE{cas_number}_{submission.email}_{filename}_{date_formatted}"
    else:
        display_name = f"CASE{cas_number}_{submission.email}_{date_formatted}"
    
    return CaseResponse(
        id=submission.id,
        case_id=submission.case_id,
        cas_number=submission.cas_number,
        email=submission.email,
        phone=submission.phone,
        description=submission.description,
        submitted_at=submission.submitted_at,
        status=submission.status,
        stage=submission.stage,
        prestations=[],
        display_name=display_name,
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
    """RAG query endpoint for Ilan. Searches across all submissions for the email address."""
    try:
        from backend.services.rag_pipeline import rag_pipeline
        from backend.database.models import Query as QueryModel
        from sqlalchemy import select
        
        # Lookup submission by case_id to get email address
        submission_id = None
        submission_ids = None
        if query.case_id:
            sub_result = await db.execute(
                select(Submission).where(Submission.case_id == query.case_id)
            )
            submission = sub_result.scalar_one_or_none()
            if submission:
                submission_id = submission.id
                email = submission.email
                
                # Find ALL submissions for this email address
                all_subs_result = await db.execute(
                    select(Submission).where(Submission.email == email)
                )
                all_submissions = all_subs_result.scalars().all()
                
                # Extract all submission IDs
                submission_ids = [sub.id for sub in all_submissions]
        
        # Run RAG pipeline with submission_ids (email-scoped search)
        result = rag_pipeline.run(
            query.query, 
            filter_metadata=None,  # No longer using single submission_id filter
            submission_ids=submission_ids
        )
        
        # Save query to database with all submission_ids
        db_query = QueryModel(
            submission_id=submission_id,  # Keep first/primary submission_id for backward compatibility
            submission_ids=submission_ids,  # Store all submission_ids as JSON array
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
        
        # Calculate display name for this case
        # Load documents for this submission
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Submission).options(selectinload(Submission.documents)).where(Submission.id == submission.id)
        )
        submission = result.scalar_one()
        
        # Format date as DDMMMYY
        date_formatted = format_date_ddmmmyy(submission.submitted_at)
        
        # Each submission now has only one document (1:1 relationship)
        # Get the single document filename
        filename = ""
        if submission.documents and len(submission.documents) > 0:
            filename = submission.documents[0].filename
        
        # Get CAS number
        cas_number = submission.cas_number if submission.cas_number is not None else 0
        
        # Format: CASE{number}_{email}_{single_filename}_{date}
        if filename:
            display_name = f"CASE{cas_number}_{submission.email}_{filename}_{date_formatted}"
        else:
            display_name = f"CASE{cas_number}_{submission.email}_{date_formatted}"
        
        return CaseResponse(
            id=submission.id,
            case_id=submission.case_id,
            cas_number=submission.cas_number,
            email=submission.email,
            phone=submission.phone,
            description=submission.description,
            submitted_at=submission.submitted_at,
            status=submission.status,
            stage=submission.stage,
            prestations=[],
            display_name=display_name,
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
        
        # Calculate display name for this case
        # Load documents for this submission
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Submission).options(selectinload(Submission.documents)).where(Submission.id == submission.id)
        )
        submission = result.scalar_one()
        
        # Format date as DDMMMYY
        date_formatted = format_date_ddmmmyy(submission.submitted_at)
        
        # Each submission now has only one document (1:1 relationship)
        # Get the single document filename
        filename = ""
        if submission.documents and len(submission.documents) > 0:
            filename = submission.documents[0].filename
        
        # Get CAS number
        cas_number = submission.cas_number if submission.cas_number is not None else 0
        
        # Format: CASE{number}_{email}_{single_filename}_{date}
        if filename:
            display_name = f"CASE{cas_number}_{submission.email}_{filename}_{date_formatted}"
        else:
            display_name = f"CASE{cas_number}_{submission.email}_{date_formatted}"
        
        return CaseResponse(
            id=submission.id,
            case_id=submission.case_id,
            cas_number=submission.cas_number,
            email=submission.email,
            phone=submission.phone,
            description=submission.description,
            submitted_at=submission.submitted_at,
            status=submission.status,
            stage=submission.stage,
            prestations=[],
            display_name=display_name,
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
        
        # Get all queries for this submission or any query that includes this submission in submission_ids
        # First get queries where submission_id matches
        query_result = await db.execute(
            select(QueryModel)
            .where(QueryModel.submission_id == submission.id)
            .order_by(QueryModel.created_at.desc())
        )
        queries_by_submission_id = query_result.scalars().all()
        
        # Also get queries where submission_ids contains this submission's id
        # Get all queries and filter in Python (SQLite JSON operations are limited)
        all_queries_result = await db.execute(
            select(QueryModel)
            .order_by(QueryModel.created_at.desc())
        )
        all_queries = all_queries_result.scalars().all()
        
        # Filter queries that include this submission in submission_ids
        queries_by_submission_ids = []
        for q in all_queries:
            if q.submission_ids:
                submission_ids_list = None
                if isinstance(q.submission_ids, list):
                    submission_ids_list = q.submission_ids
                elif isinstance(q.submission_ids, str):
                    import json
                    try:
                        submission_ids_list = json.loads(q.submission_ids)
                    except (json.JSONDecodeError, TypeError):
                        submission_ids_list = None
                
                if submission_ids_list and submission.id in submission_ids_list:
                    queries_by_submission_ids.append(q)
        
        # Combine and deduplicate queries
        seen_query_ids = set()
        all_queries_combined = []
        for q in queries_by_submission_id:
            if q.id not in seen_query_ids:
                all_queries_combined.append(q)
                seen_query_ids.add(q.id)
        for q in queries_by_submission_ids:
            if q.id not in seen_query_ids:
                all_queries_combined.append(q)
                seen_query_ids.add(q.id)
        
        # Sort by created_at descending
        all_queries_combined.sort(key=lambda x: x.created_at, reverse=True)
        
        # Convert to response format
        query_responses = []
        for q in all_queries_combined:
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
            
            # Parse submission_ids from JSON (stored as TEXT in SQLite)
            submission_ids_list = None
            if q.submission_ids:
                if isinstance(q.submission_ids, list):
                    submission_ids_list = q.submission_ids
                elif isinstance(q.submission_ids, str):
                    # If stored as JSON string, parse it
                    import json
                    try:
                        submission_ids_list = json.loads(q.submission_ids)
                    except (json.JSONDecodeError, TypeError):
                        submission_ids_list = None
            
            query_responses.append(QueryHistoryResponse(
                id=q.id,
                query_text=q.query_text,
                response_text=q.response_text,
                citations=citations,
                retrieved_chunk_ids=q.retrieved_chunk_ids,
                submission_id=q.submission_id,
                submission_ids=submission_ids_list,
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

