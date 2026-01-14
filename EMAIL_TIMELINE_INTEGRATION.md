# EMAIL TIMELINE INTEGRATION - MANUAL STEPS

## Step 1: Update backend/api/routes.py

### Add helper function after line 46 (after format_date_ddmmmyy):

```python
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
```

### In the `get_cases` function, around line 618, BEFORE the line:
```python
date_formatted = format_date_ddmmmyy(primary_sub.get("submitted_at"))
```

### ADD:
```python
# Fetch email timeline
email_messages = await fetch_case_emails(
    primary_sub["_id"],
    primary_sub["email"],
    primary_sub["submitted_at"],
    db
)
```

### Then in the CaseResponse() creation (around line 638), change:
```python
documents=all_documents
```

### TO:
```python
documents=all_documents,
emails=email_messages
```

---

## Frontend Changes Already Complete
- ✅ EmailMessageSchema added to schemas.py
- ✅ emails field added to CaseResponse schema

##Frontend UI will need update
I'll create that component now...
