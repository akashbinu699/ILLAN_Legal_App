"""
Helper function to fetch emails for a case.
Add this to routes.py to fetch email timeline.
"""

async def fetch_case_emails(primary_sub_id: str, primary_sub_email: str, primary_submitted_at, db):
    """Fetch all email messages for a case."""
    from backend.api.schemas import EmailMessageSchema
    
    case_emails = await db.queries.find({
        "submission_id": str(primary_sub_id),
        "is_email": True
    }).sort("created_at", 1).to_list(None)
    
    email_messages = [
        EmailMessageSchema(
            id=str(e["_id"]),
            subject=e.get("query_text", "").replace("EMAIL: ", ""),
            body=e.get("response_text", ""),
            from_email=e.get("from_email", primary_sub_email),
            created_at=e.get("created_at", primary_submitted_at),
            gmail_message_id=e.get("gmail_message_id")
        )
        for e in case_emails
    ]
    
    return email_messages


#  In get_cases(), before the CaseResponse creation (line ~635), add:
#
#  email_messages = await fetch_case_emails(
#      primary_sub["_id"],
#      primary_sub["email"],
#      primary_sub["submitted_at"],
#      db
#  )
#
#  Then add to CaseResponse():
#      emails=email_messages
