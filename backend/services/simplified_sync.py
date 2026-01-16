"""
SIMPLIFIED GMAIL SYNC LOGIC
1 Email Address = 1 Case (Forever)

This is a simplified replacement for process_gmail_sync in routes.py
"""

async def process_gmail_sync_simplified(days: int, db):
    """Simplified sync logic: 1 email address = 1 case."""
    from backend.services.gmail_service import gmail_service
    from backend.config import settings
    from datetime import datetime
    
    print("=== STARTING SIMPLIFIED GMAIL SYNC ===")
    print("Rule: 1 Email Address = 1 Case")
    
    try:
        # Search for new case notification emails
        # Search for ALL unprocessed messages, not just "New Case" subjects
        # This ensures we catch replies like "Re: Update" or "Question"
        query = '-label:ILAN_PROCESSED'
        
        print(f"[SYNC] Gmail query: {query}")
        # Fetch up to 200 messages to avoid timeouts, can be increased
        messages = gmail_service.get_messages(query=query, max_results=200)
        
        if not messages:
            print("[SYNC] No new messages found.")
            return {
                "status": "success",
                "total_found": 0,
                "processed": 0,
                "new_cases": 0
            }
        
        print(f"[SYNC] Found {len(messages)} messages. Fetching details...")
        
        # Fetch and sort by date (oldest first)
        full_messages = []
        for m in messages:
            full = gmail_service.get_message(m['id'])
            if full:
                full_messages.append(full)
        
        full_messages.sort(key=lambda x: int(x['internalDate']))
        
        processed_count = 0
        new_cases_count = 0

        for full_msg in full_messages:
            msg_id = full_msg['id']
            
            # Skip if already processed (check query history)
            existing = await db.queries.find_one({"gmail_message_id": msg_id})
            if existing:
                print(f"[SYNC] Message {msg_id[:8]}... already processed. Skipping.")
                continue

            # Extract client email from message body or sender
            parsed = gmail_service.parse_message_content(full_msg)
            client_email = parsed.get('form_data', {}).get('CLIENT EMAIL')
            
            if not client_email:
                # Fall back to sender email
                client_email = parsed.get('from', '')
                if '<' in client_email:
                    client_email = client_email.split('<')[-1].replace('>', '').strip()
            
            # Normalize email
            if client_email:
                client_email = client_email.lower().strip()
            
            # Validate email (skip if empty or lawyer's own email)
            if not client_email:
                print(f"[SYNC] Skipping message {msg_id[:8]}... - No client email found")
                gmail_service.add_label_to_message(msg_id, "ILAN_PROCESSED")
                continue
                
            if settings.notification_email and settings.notification_email.lower() in client_email.lower():
                print(f"[SYNC] Skipping message {msg_id[:8]}... - It's from lawyer email")
                gmail_service.add_label_to_message(msg_id, "ILAN_PROCESSED")
                continue
            
            print(f"\n[SYNC] Processing email from: {client_email}")
            
            # === CORE SIMPLIFIED LOGIC ===
            # Check if case exists for this email address
            existing_case = await db.submissions.find_one({"email": client_email})
            
            if existing_case:
                # Case exists - reuse it
                case_id = existing_case['case_id']
                cas_number = existing_case.get('cas_number', 1)
                print(f"[SYNC] ✓ Existing case found: {case_id}")
                is_new_case = False
            else:
                # New email address - create new case
                timestamp = datetime.fromtimestamp(int(full_msg['internalDate'])/1000)
                date_str = timestamp.strftime("%d%b%y").upper()
                
                # Generate global cas_number
                pipeline = [{"$group": {"_id": None, "max_cas": {"$max": "$cas_number"}}}]
                cursor = db.submissions.aggregate(pipeline)
                res = await cursor.to_list(length=1)
                max_cas = res[0]["max_cas"] if res and "max_cas" in res[0] else 0
                cas_number = (max_cas + 1) if max_cas is not None else 1
                
                case_id = f"{client_email}_{date_str}"
                print(f"[SYNC] ✓ New case created: {case_id} (CAS#{cas_number})")
                is_new_case = True
                new_cases_count += 1
            
            # Process the message and attachments
            await process_single_message(
                full_msg=full_msg,
                case_id=case_id,
                cas_number=cas_number,
                client_email=client_email,
                is_new_case=is_new_case,
                db=db
            )
            
            processed_count += 1
            print(f"[SYNC] ✓ Message processed successfully")
                    
        print(f"\n=== SYNC COMPLETE ===")
        print(f"Total found: {len(messages)}")
        print(f"Processed: {processed_count}")
        print(f"New cases created: {new_cases_count}")
        
        return {
            "status": "success",
            "total_found": len(messages),
            "processed": processed_count,
            "new_cases": new_cases_count
        }
        
    except Exception as e:
        print(f"[SYNC] ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


async def process_single_message(full_msg, case_id, cas_number, client_email, is_new_case, db):
    """Process a single email message and its attachments."""
    from backend.services.gmail_service import gmail_service
    from backend.services.llm_service import llm_service
    from backend.services.processing_pipeline import processing_pipeline
    from backend.database.mongo_models import SubmissionModel, DocumentModel, QueryModel
    import base64
    import os
    from datetime import datetime
    import asyncio
    
    msg_id = full_msg['id']
    content = gmail_service.parse_message_content(full_msg)
    attachments = gmail_service.extract_attachments(full_msg)
    timestamp = datetime.fromtimestamp(int(full_msg['internalDate'])/1000)
    
    phone = content.get('form_data', {}).get('PHONE', '')
    description = content.get('form_data', {}).get('DESCRIPTION', content['body'])
    
    # If this is a new case, create the primary submission
    if is_new_case:
        # Extract text from attachments for AI analysis
        files_content_for_llm = []
        if attachments:
            for att in attachments:
                try:
                    mime = att.get('mimeType', '')
                    if 'pdf' in mime:
                        import io
                        from pypdf import PdfReader
                        pdf_bytes = base64.b64decode(att['base64'])
                        reader = PdfReader(io.BytesIO(pdf_bytes))
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        if text.strip():
                            files_content_for_llm.append(text)
                    elif 'text' in mime:
                        text = base64.b64decode(att['base64']).decode('utf-8', errors='ignore')
                        files_content_for_llm.append(text)
                except Exception as e:
                    print(f"[SYNC] Failed to extract text from attachment: {e}")
        
        # Analyze with Gemini
        try:
            analysis = await llm_service.analyze_case_stage_and_benefits(description, files_content=files_content_for_llm)
            detected_stage = analysis.get("stage", "RAPO")
            detected_prestations = analysis.get("benefits", [])
        except Exception as ex:
            print(f"[SYNC] Gemini analysis failed: {ex}")
            detected_stage = "RAPO"
            detected_prestations = []
        
        # Create primary submission
        new_sub = SubmissionModel(
            case_id=case_id,
            cas_number=cas_number,
            email=client_email,
            phone=phone,
            description=description,
            submitted_at=timestamp,
            status="NEW",
            stage=detected_stage,
            document=DocumentModel(filename="Email Body", mime_type="text/plain")
        )
        ns_dict = new_sub.model_dump(by_alias=True, exclude_none=True)
        ns_dict["prestations_detected"] = detected_prestations
        
        insertion_result = await db.submissions.insert_one(ns_dict)
        sub_id = str(insertion_result.inserted_id)
        print(f"[SYNC] Created primary submission with ID: {sub_id}")
    else:
        # Existing case - get the primary submission ID
        primary_sub = await db.submissions.find_one({"case_id": case_id}, sort=[("submitted_at", 1)])
        sub_id = str(primary_sub['_id'])
        cas_number = primary_sub.get('cas_number', 1)
        detected_stage = primary_sub.get('stage', 'RAPO')
    
    # Store email as query/interaction
    email_query = QueryModel(
        submission_id=sub_id,
        submission_ids=[sub_id],
        query_text=f"EMAIL: {content['subject']}",
        response_text=content['body'],
        created_at=timestamp
    )
    q_dict = email_query.model_dump(by_alias=True, exclude_none=True)
    q_dict["gmail_message_id"] = msg_id
    q_dict["is_email"] = True
    q_dict["from_email"] = content['from']
    try:
        await db.queries.insert_one(q_dict)
        print(f"[SYNC] Saved email query for {client_email}")
    except Exception as e:
        print(f"[SYNC] Failed to save email query: {e}")
    
    # Process attachments
    if attachments:
        att_counter = await db.submissions.count_documents({
            "case_id": case_id,
            "description": {"$regex": "^Gmail Attachment"}
        })
        
        for att in attachments:
            att_counter += 1
            original_name = att['filename']
            ext = os.path.splitext(original_name)[1] or ".bin"
            new_filename = f"{case_id}-doc{att_counter}{ext}"
            
            att_sub_doc = SubmissionModel(
                case_id=case_id,
                cas_number=cas_number,
                email=client_email,
                phone=phone,
                description=f"Gmail Attachment: {original_name} (from {content['subject']})",
                submitted_at=timestamp,
                status="NEW",
                stage=detected_stage,
                document=DocumentModel(
                    filename=new_filename,
                    mime_type=att['mime_type'],
                    file_content=att['base64']
                )
            )
            as_dict = att_sub_doc.model_dump(by_alias=True, exclude_none=True)
            as_res = await db.submissions.insert_one(as_dict)
            
            # Trigger processing
            asyncio.create_task(processing_pipeline.process_submission(
                str(as_res.inserted_id),
                [{"name": new_filename, "mimeType": att['mime_type'], "base64": att['base64']}],
                db
            ))
    
    # Mark as processed in Gmail
    gmail_service.add_label_to_message(msg_id, "ILAN_PROCESSED")


# To integrate: Replace process_gmail_sync in routes.py with process_gmail_sync_simplified
