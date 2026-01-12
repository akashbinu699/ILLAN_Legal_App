"""API routes for the backend (MongoDB version)."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import asyncio
from backend.database.db import get_db
from backend.database.mongo_models import SubmissionModel, DocumentModel, QueryModel
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
    EmailGroupResponse,
    PrestationSchema
)
from datetime import datetime
from collections import defaultdict
import json
import base64
from bson import ObjectId
from backend.services.gmail_service import gmail_service
from backend.config import settings

router = APIRouter()

def format_date_ddmmmyy(dt: datetime) -> str:
    """Format datetime as DDMMMYY (e.g., 01JAN25)."""
    if not dt: return ""
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
    db = Depends(get_db)
):
    """
    Receive form submission from frontend.
    Step 1: Skip direct saving to DB.
    Step 2: Send email notification first.
    The case will be created in the DB when the Gmail sync/webhook occurs.
    """
    try:
        now = datetime.now()
        case_id = f"CAS_{now.strftime('%d-%m-%y_%H:%M:%S')}"
        
        # Trigger Gmail notification immediately
        # We await here to ensure it is sent successfully as the "primary" action
        await send_submission_notification(submission, case_id)
        
        # Return a response indicating the case is initiated
        return SubmissionResponse(
            id="pending", # ID will be assigned after sync
            case_id=case_id,
            email=submission.email,
            phone=submission.phone,
            description=submission.description,
            submitted_at=datetime.utcnow(),
            status="PENDING_SYNC",
            stage="NEW"
        )
    except Exception as e:
        print(f"Error in submit_case: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing submission: {str(e)}")

async def process_in_background(original_submission, created_submissions, db):
    try:
        from backend.services.processing_pipeline import processing_pipeline
        for idx, sub in enumerate(created_submissions):
            file_data = original_submission.files[idx]
            await processing_pipeline.process_submission(
                str(sub.id),
                [{"name": file_data.name, "mimeType": file_data.mimeType, "base64": file_data.base64}],
                db
            )
    except Exception as e:
        print(f"Background processing error: {e}")

async def send_submission_notification(submission, case_id):
    """Send an email notification about a new submission."""
    try:
        if not settings.notification_email:
            print("[GMAIL] No notification_email set in config, skipping notification")
            return

        subject = f"NEW LEGAL CASE: {case_id} - {submission.email}"
        body = f"""
        A new legal case has been submitted via the client interface.
        
        CASE ID: {case_id}
        CLIENT EMAIL: {submission.email}
        PHONE: {submission.phone}
        
        DESCRIPTION:
        {submission.description}
        
        {len(submission.files)} document(s) attached.
        
        View more details in the Lawyer Space.
        """
        
        success = gmail_service.send_email_with_attachments(
            to_email=settings.notification_email,
            subject=subject,
            body=body,
            attachments=[{"name": f.name, "mimeType": f.mimeType, "base64": f.base64} for f in submission.files]
        )
        
        if success:
            print(f"[GMAIL] Notification sent for {case_id}")
        else:
            print(f"[GMAIL] Failed to send notification for {case_id}")
            
    except Exception as e:
        print(f"Error in send_submission_notification: {e}")

@router.post("/sync-gmail-case/{case_id}")
async def sync_gmail_for_case(case_id: str, db = Depends(get_db)):
    """
    Sync Gmail messages containing the case_id.
    If the case doesn't exist in DB, create it from the email data.
    Uses Gemini to detect stage and prestations.
    """
    try:
        from backend.services.llm_service import llm_service
        from backend.services.processing_pipeline import processing_pipeline

        # 1. Search Gmail for this case_id
        query = f'"{case_id}"'
        messages = gmail_service.get_messages(query=query, max_results=10)
        
        sync_results = []
        new_case_created_info = None
        
        for msg_info in messages:
            msg = gmail_service.get_message(msg_info['id'])
            if not msg: continue
            
            # Check if we already synced this message
            existing_query = await db.queries.find_one({"gmail_message_id": msg['id']})
            if existing_query: continue
            
            content = gmail_service.parse_message_content(msg)
            attachments = gmail_service.extract_attachments(msg)
            timestamp = datetime.fromtimestamp(int(msg['internalDate'])/1000)
            
            # 2. Check if case exists in DB (it might not if this is the first sync after submission)
            sub = await db.submissions.find_one({"case_id": case_id})
            
            if not sub:
                # CREATE NEW CASE FROM EMAIL DATA
                print(f"[SYNC] Case {case_id} not found in DB. Reconstructing from email content...")
                
                # Parse form data from email body (using the helper in gmail_service)
                form_data = content.get('form_data', {})
                email = form_data.get('CLIENT EMAIL', content['from'])
                phone = form_data.get('PHONE', "")
                description = form_data.get('DESCRIPTION', content['body'])
                
                # Use Gemini to detect stage and type
                print(f"[SYNC] Calling Gemini to analyze case stage/type...")
                analysis_prompt = f"""
                Tu es un expert en droit administratif français. Analyse cette description de dossier :
                
                DESCRIPTION: {description}
                
                Détermine :
                1. L'étape du dossier (CONTROL, RAPO, ou LITIGATION).
                2. Les types de prestations sociales concernées (ex: RSA, APL, Prime d'activité, etc.).
                
                Réponds UNIQUEMENT au format JSON comme ceci :
                {{"stage": "STAGE_NAME", "prestations": ["P1", "P2"]}}
                """
                try:
                    analysis_raw = await llm_service.generate(analysis_prompt)
                    print(f"[SYNC] Gemini Raw Response: {analysis_raw}")
                    # Use regex to find the JSON block in case there is markdown wrapper
                    import re
                    match = re.search(r'\{.*\}', analysis_raw, re.DOTALL)
                    if match:
                        analysis = json.loads(match.group())
                        detected_stage = analysis.get("stage", "RAPO")
                        detected_prestations = analysis.get("prestations", [])
                    else:
                        detected_stage = "RAPO"
                        detected_prestations = []
                except Exception as ex:
                    print(f"[SYNC] Gemini analysis failed: {ex}")
                    detected_stage = "RAPO"
                    detected_prestations = []

                # Determine CAS number (incrementing)
                pipeline = [{"$group": {"_id": None, "max_cas": {"$max": "$cas_number"}}}]
                cursor = db.submissions.aggregate(pipeline)
                res = await cursor.to_list(length=1)
                max_cas = res[0]["max_cas"] if res and "max_cas" in res[0] else 0
                cas_number = (max_cas + 1) if max_cas is not None else 1

                # Create the primary submission record
                new_sub = SubmissionModel(
                    case_id=case_id,
                    cas_number=cas_number,
                    email=email,
                    phone=phone,
                    description=description,
                    submitted_at=timestamp,
                    status="NEW",
                    stage=detected_stage,
                    document=DocumentModel(filename="Email Body", mime_type="text/plain")
                )
                ns_dict = new_sub.model_dump(by_alias=True, exclude_none=True)
                # Store detected prestations (as a simple list for metadata)
                ns_dict["prestations_detected"] = detected_prestations
                
                insertion_result = await db.submissions.insert_one(ns_dict)
                sub_id = str(insertion_result.inserted_id)
                new_case_created_info = {"id": sub_id, "cas_number": cas_number}
                print(f"[SYNC] Successfully created new case {case_id} in DB.")
                
                # Fetch the newly created sub to use its data for attachments
                sub = ns_dict 
                sub["_id"] = insertion_result.inserted_id
            else:
                sub_id = str(sub["_id"])

            # 3. Store the email as a Query/Interaction record
            email_query = QueryModel(
                submission_id=sub_id,
                submission_ids=[sub_id],
                query_text=f"EMAIL: {content['subject']}",
                response_text=content['body'],
                created_at=timestamp
            )
            q_dict = email_query.model_dump(by_alias=True, exclude_none=True)
            q_dict["gmail_message_id"] = msg['id']
            q_dict["is_email"] = True
            q_dict["from_email"] = content['from']
            await db.queries.insert_one(q_dict)
            
            sync_results.append({
                "id": msg['id'],
                "subject": content['subject'],
                "from": content['from'],
                "date": content['date']
            })
            
            # 4. Process attachments as individual sub-submissions for this case
            if attachments:
                for att in attachments:
                    att_sub_doc = SubmissionModel(
                        case_id=case_id,
                        cas_number=sub["cas_number"],
                        email=content['from'],
                        phone="",
                        description=f"Gmail Attachment: {att['filename']} (from {content['subject']})",
                        submitted_at=timestamp,
                        status="NEW",
                        stage=sub.get("stage", "RAPO"),
                        document=DocumentModel(filename=att['filename'], mime_type=att['mime_type'])
                    )
                    as_dict = att_sub_doc.model_dump(by_alias=True, exclude_none=True)
                    as_res = await db.submissions.insert_one(as_dict)
                    
                    # Trigger processing for the attachment content
                    asyncio.create_task(processing_pipeline.process_submission(
                        str(as_res.inserted_id),
                        [{"name": att['filename'], "mimeType": att['mime_type'], "base64": att['base64']}],
                        db
                    ))
        
        return {
            "status": "success",
            "synced_count": len(sync_results),
            "new_case_created": new_case_created_info is not None,
            "messages": sync_results
        }
    except Exception as e:
        print(f"Error in sync_gmail_for_case: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-all-gmail")
async def sync_all_gmail(days: int = 7, db = Depends(get_db)):
    """
    Global sync: Search Gmail for all messages containing "CAS_" from the last X days.
    Processes any message that hasn't been synced yet.
    """
    try:
        # Search for messages with CAS_ prefix (any case ID)
        # Gmail query uses 'after:YYYY/MM/DD' to limit time range
        from datetime import datetime, timedelta
        query = 'subject:"NEW LEGAL CASE"'
        
        print(f"[SYNC-ALL] Searching Gmail with query: {query}")
        messages = gmail_service.get_messages(query=query, max_results=100)
        
        processed_count = 0
        new_cases_count = 0
        
        for msg_info in messages:
            msg_id = msg_info['id']
            
            # Skip if already in DB
            existing = await db.queries.find_one({"gmail_message_id": msg_id})
            if existing:
                continue
            
            # Fetch full message
            full_msg = gmail_service.get_message(msg_id)
            if not full_msg: continue
            
            # Extract Case ID from Subject
            subject = next((h['value'] for h in full_msg['payload']['headers'] if h['name'].lower() == 'subject'), '')
            import re
            match = re.search(r'CAS_[\d\-_:]+', subject)
            
            if match:
                case_id = match.group(0)
                print(f"[SYNC-ALL] Found new email for {case_id}. Processing...")
                
                # Use the existing sync logic for this specific case
                result = await sync_gmail_for_case(case_id, db)
                processed_count += 1
                if result.get("new_case_created"):
                    new_cases_count += 1
                    
        return {
            "status": "success",
            "total_found": len(messages),
            "processed": processed_count,
            "new_cases": new_cases_count
        }
    except Exception as e:
        print(f"Error in sync_all_gmail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases", response_model=List[EmailGroupResponse])
async def get_cases(
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_db)
):
    """Retrieve all cases grouped by email address."""
    cursor = db.submissions.find().sort("submitted_at", -1).skip(skip).limit(limit)
    submissions = await cursor.to_list(length=limit)
    
    email_groups = defaultdict(list)
    for sub in submissions:
        email_groups[sub.get("email")].append(sub)
        
    email_group_list = []
    for email, subs in email_groups.items():
        subs_sorted_asc = sorted(subs, key=lambda s: (s.get("submitted_at"), s.get("case_id"), str(s.get("_id"))))
        cas_number = subs_sorted_asc[0].get("cas_number", 0)
        
        case_id_groups = defaultdict(list)
        for sub in subs_sorted_asc:
            case_id_groups[sub.get("case_id")].append(sub)
            
        cases_with_numbers = []
        sorted_case_groups = sorted(
            case_id_groups.items(),
            key=lambda x: min(s.get("submitted_at") for s in x[1]) if x[1] else datetime.min
        )
        
        for case_id, case_subs in sorted_case_groups:
             case_subs_sorted = sorted(case_subs, key=lambda s: str(s.get("_id")))
             for sub in case_subs_sorted:
                 date_formatted = format_date_ddmmmyy(sub.get("submitted_at"))
                 filename = sub.get("document", {}).get("filename", "")
                 display_name = f"CASE{cas_number}_{email}_{filename}_{date_formatted}" if filename else f"CASE{cas_number}_{email}_{date_formatted}"
                 
                 cases_with_numbers.append(CaseResponse(
                     id=str(sub["_id"]),
                     case_id=sub["case_id"],
                     cas_number=cas_number,
                     email=sub["email"],
                     phone=sub.get("phone", ""),
                     description=sub.get("description", ""),
                     submitted_at=sub["submitted_at"],
                     status=sub["status"],
                     stage=sub["stage"],
                     prestations=[PrestationSchema(name=p, isAccepted=True) for p in (sub.get('prestations_detected') or [])],
                     display_name=display_name,
                     generatedEmailDraft=sub.get("generated_email_draft"),
                     generatedAppealDraft=sub.get("generated_appeal_draft"),
                     emailPrompt=sub.get("email_prompt"),
                     appealPrompt=sub.get("appeal_prompt")
                 ))
        
        cases_sorted_desc = sorted(cases_with_numbers, key=lambda c: c.submitted_at, reverse=True)
        email_group_list.append(EmailGroupResponse(
            email=email,
            cas_number=cas_number,
            cas_display_name=email,
            cases=cases_sorted_desc
        ))
        
    email_group_list.sort(key=lambda g: g.cases[0].submitted_at if g.cases else datetime.min, reverse=True)
    return email_group_list

@router.get("/case/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db = Depends(get_db)):
    sub = await db.submissions.find_one({"case_id": case_id})
    if not sub:
        try:
            sub = await db.submissions.find_one({"_id": ObjectId(case_id)})
        except:
            pass
    if not sub:
         raise HTTPException(status_code=404, detail="Case not found")
         
    date_formatted = format_date_ddmmmyy(sub["submitted_at"])
    filename = sub.get("document", {}).get("filename", "")
    cas_number = sub.get("cas_number", 0)
    display_name = f"CASE{cas_number}_{sub['email']}_{filename}_{date_formatted}" if filename else f"CASE{cas_number}_{sub['email']}_{date_formatted}"

    return CaseResponse(
        id=str(sub["_id"]),
        case_id=sub["case_id"],
        cas_number=cas_number,
        email=sub["email"],
        phone=sub.get("phone", ""),
        description=sub.get("description", ""),
        submitted_at=sub["submitted_at"],
        status=sub["status"],
        stage=sub["stage"],
        prestations=[PrestationSchema(name=p, isAccepted=True) for p in (sub.get('prestations_detected') or [])],
        display_name=display_name,
        generatedEmailDraft=sub.get("generated_email_draft"),
        generatedAppealDraft=sub.get("generated_appeal_draft"),
        emailPrompt=sub.get("email_prompt"),
        appealPrompt=sub.get("appeal_prompt")
    )

@router.patch("/case/{case_id}", response_model=CaseResponse)
async def update_case(case_id: str, update: CaseUpdate, db = Depends(get_db)):
    sub = await db.submissions.find_one({"case_id": case_id})
    if not sub:
        try:
             sub = await db.submissions.find_one({"_id": ObjectId(case_id)})
        except:
             pass
    if not sub:
        raise HTTPException(status_code=404, detail="Case not found")
        
    update_data = {}
    if update.generatedEmailDraft is not None: update_data["generated_email_draft"] = update.generatedEmailDraft
    if update.generatedAppealDraft is not None: update_data["generated_appeal_draft"] = update.generatedAppealDraft
    if update.emailPrompt is not None: update_data["email_prompt"] = update.emailPrompt
    if update.appealPrompt is not None: update_data["appeal_prompt"] = update.appealPrompt
    if update.stage is not None: update_data["stage"] = update.stage
    if update.status is not None: update_data["status"] = update.status
    
    if update_data:
        await db.submissions.update_one({"_id": sub["_id"]}, {"$set": update_data})
        sub = await db.submissions.find_one({"_id": sub["_id"]})
        
    date_formatted = format_date_ddmmmyy(sub["submitted_at"])
    filename = sub.get("document", {}).get("filename", "")
    cas_number = sub.get("cas_number", 0)
    display_name = f"CASE{cas_number}_{sub['email']}_{filename}_{date_formatted}" if filename else f"CASE{cas_number}_{sub['email']}_{date_formatted}"

    return CaseResponse(
        id=str(sub["_id"]),
        case_id=sub["case_id"],
        cas_number=cas_number,
        email=sub["email"],
        phone=sub.get("phone", ""),
        description=sub.get("description", ""),
        submitted_at=sub["submitted_at"],
        status=sub["status"],
        stage=sub["stage"],
        prestations=[PrestationSchema(name=p, isAccepted=True) for p in (sub.get('prestations_detected') or [])],
        display_name=display_name,
        generatedEmailDraft=sub.get("generated_email_draft"),
        generatedAppealDraft=sub.get("generated_appeal_draft"),
        emailPrompt=sub.get("email_prompt"),
        appealPrompt=sub.get("appeal_prompt")
    )

@router.post("/case/{case_id}/generate-drafts", response_model=CaseResponse)
async def generate_drafts(case_id: str, db = Depends(get_db)):
    sub = await db.submissions.find_one({"case_id": case_id})
    if not sub:
        raise HTTPException(status_code=404, detail="Case not found")

    from backend.services.llm_service import llm_service
    updates = {}
    
    if not sub.get("generated_email_draft"):
        prompt = f"Generate a professional email draft for a legal case.\n\nCase ID: {sub['case_id']}\nClient Email: {sub['email']}\nClient Phone: {sub['phone']}\nCase Description: {sub['description']}\nStage: {sub['stage']}\n"
        try:
             draft = await llm_service.generate(prompt)
             updates["generated_email_draft"] = draft
             updates["email_prompt"] = prompt
        except Exception as e:
            print(f"Error generating email: {e}")

    if not sub.get("generated_appeal_draft"):
        prompt = f"Generate a professional appeal draft for a legal case.\n\nCase ID: {sub['case_id']}\nDescription: {sub['description']}\nStage: {sub['stage']}\n"
        try:
             draft = await llm_service.generate(prompt)
             updates["generated_appeal_draft"] = draft
             updates["appeal_prompt"] = prompt
        except Exception as e:
            print(f"Error generating appeal: {e}")

    if updates:
        await db.submissions.update_one({"_id": sub["_id"]}, {"$set": updates})
        sub = await db.submissions.find_one({"_id": sub["_id"]})

    date_formatted = format_date_ddmmmyy(sub["submitted_at"])
    filename = sub.get("document", {}).get("filename", "")
    cas_number = sub.get("cas_number", 0)
    display_name = f"CASE{cas_number}_{sub['email']}_{filename}_{date_formatted}" if filename else f"CASE{cas_number}_{sub['email']}_{date_formatted}"

    return CaseResponse(
        id=str(sub["_id"]),
        case_id=sub["case_id"],
        cas_number=cas_number,
        email=sub["email"],
        phone=sub.get("phone", ""),
        description=sub.get("description", ""),
        submitted_at=sub["submitted_at"],
        status=sub["status"],
        stage=sub["stage"],
        prestations=[PrestationSchema(name=p, isAccepted=True) for p in (sub.get('prestations_detected') or [])],
        display_name=display_name,
        generatedEmailDraft=sub.get("generated_email_draft"),
        generatedAppealDraft=sub.get("generated_appeal_draft"),
        emailPrompt=sub.get("email_prompt"),
        appealPrompt=sub.get("appeal_prompt")
    )

@router.post("/case/{case_id}/generate-draft", response_model=GenerateDraftResponse)
async def generate_single_draft(case_id: str, request: GenerateDraftRequest, db = Depends(get_db)):
    sub = await db.submissions.find_one({"case_id": case_id})
    if not sub:
        raise HTTPException(status_code=404, detail="Case not found")
        
    from backend.services.llm_service import llm_service
    try:
        draft = await llm_service.generate(request.prompt)
        updates = {}
        if request.draft_type == 'email':
            updates["generated_email_draft"] = draft
            updates["email_prompt"] = request.prompt
        elif request.draft_type == 'appeal':
            updates["generated_appeal_draft"] = draft
            updates["appeal_prompt"] = request.prompt
            
        await db.submissions.update_one({"_id": sub["_id"]}, {"$set": updates})
        return GenerateDraftResponse(draft=draft, prompt=request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_rag(query: QueryRequest, db = Depends(get_db)):
    from backend.services.rag_pipeline import rag_pipeline
    
    submission_ids = []
    submission_id = None
    
    if query.case_id:
        sub = await db.submissions.find_one({"case_id": query.case_id})
        if sub:
            submission_id = str(sub["_id"])
            cursor = db.submissions.find({"email": sub["email"]})
            all_subs = await cursor.to_list(length=1000)
            submission_ids = [str(s["_id"]) for s in all_subs] # Use ObjectIds as strings
            
    result = await rag_pipeline.run(query.query, filter_metadata=None, submission_ids=submission_ids)
    
    # Save query
    query_doc = QueryModel(
        submission_id=submission_id,
        submission_ids=submission_ids,
        query_text=query.query,
        response_text=result['answer'],
        citations=result.get('citations', []),
        retrieved_chunk_ids=[chunk.get('id') for chunk in result.get('retrieved_chunks', [])]
    )
    
    q_dict = query_doc.model_dump(by_alias=True, exclude_none=True)
    insert_res = await db.queries.insert_one(q_dict)
    
    # Format citations (reused logic from original)
    return QueryResponse(
        response=result['answer'],
        citations=query_doc.citations, # Simplified for now
        retrieved_chunks=len(result.get('retrieved_chunks', [])),
        query_id=str(insert_res.inserted_id)
    )

@router.get("/case/{case_id}/queries", response_model=List[QueryHistoryResponse])
async def get_case_queries(case_id: str, db = Depends(get_db)):
    sub = await db.submissions.find_one({"case_id": case_id})
    if not sub:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Find queries related to this submission ID or list
    sub_id = str(sub["_id"])
    cursor = db.queries.find({
        "$or": [
            {"submission_id": sub_id},
            {"submission_ids": sub_id}
        ]
    }).sort("created_at", -1)
    
    queries = await cursor.to_list(length=100)
    
    response = []
    for q in queries:
        response.append(QueryHistoryResponse(
            id=str(q["_id"]),
            query_text=q["query_text"],
            response_text=q["response_text"],
            citations=q.get("citations", []),
            retrieved_chunk_ids=q.get("retrieved_chunk_ids", []),
            submission_id=q.get("submission_id"),
            submission_ids=q.get("submission_ids"),
            created_at=q["created_at"]
        ))
    return response

@router.post("/detect-stage", response_model=StageDetectionResponse)
async def detect_stage(request: StageDetectionRequest):
    """Detect the stage and type of case using Gemini analysis."""
    try:
        from backend.services.llm_service import llm_service
        
        prompt = f"""
        Tu es un expert en droit administratif français. Analyse cette description de dossier :
        
        DESCRIPTION: {request.description}
        
        Détermine :
        1. L'étape du dossier (CONTROL, RAPO, ou LITIGATION).
        2. Les types de prestations sociales concernées (ex: RSA, APL, Prime d'activité, etc.).
        
        Réponds UNIQUEMENT au format JSON comme ceci :
        {{"stage": "STAGE_NAME", "prestations": ["P1", "P2"]}}
        """
        
        analysis_raw = await llm_service.generate(prompt)
        
        # Parse JSON from response
        import re
        match = re.search(r'\{.*\}', analysis_raw, re.DOTALL)
        if match:
            analysis = json.loads(match.group())
            stage = analysis.get("stage", "RAPO")
            prestations_list = analysis.get("prestations", [])
            
            # Convert simple strings to PrestationSchema objects
            prestations = [PrestationSchema(name=p, isAccepted=True) for p in prestations_list]
        else:
            stage = "RAPO"
            prestations = []
            
        return StageDetectionResponse(
            stage=stage,
            prestations=prestations
        )
    except Exception as e:
        print(f"Error in detect_stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
