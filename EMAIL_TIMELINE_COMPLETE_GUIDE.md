# EMAIL TIMELINE FEATURE - COMPLETE IMPLEMENTATION GUIDE

## ✅ Already Completed

1. **Backend Schema** (`backend/api/schemas.py`)
   - ✅ Added `EmailMessageSchema` class
   - ✅ Added `emails` field to `CaseResponse`

2. **Frontend Component** (`frontend/src/components/EmailTimeline.tsx`)
   - ✅ Created with navigation between emails
   - ✅ Shows subject, body, timestamp, sender
   - ✅ Arrow buttons + dot navigation
   - ✅ Quick jump timeline

---

## 🔧 Manual Integration Required

### STEP 1: Update Backend Routes (`backend/api/routes.py`)

#### 1a. Add helper function after line 46:

Find this line (around line 46):
```python
    return f"{day}{month}{year}"
```

Add AFTER it:
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

#### 1b. Update get_cases function (around line 618):

Find this section in the `get_cases` function:
```python
              date_formatted = format_date_ddmmmyy(primary_sub.get("submitted_at"))
              display_name = primary_sub["case_id"]
```

Add BEFORE it:
```python
              # Fetch email timeline
              email_messages = await fetch_case_emails(
                  primary_sub["_id"],
                  primary_sub["email"],
                  primary_sub["submitted_at"],
                  db
              )
              
```

#### 1c. Update CaseResponse creation (around line 638):

Find:
```python
                  documents=all_documents
              ))
```

Change TO:
```python
                  documents=all_documents,
                  emails=email_messages
              ))
```

---

### STEP 2: Update Frontend Types (`frontend/src/types.ts`)

Add this type definition:
```typescript
export interface EmailMessage {
  id: string;
  subject: string;
  body: string;
  from_email: string;
  created_at: string;
  gmail_message_id?: string;
}
```

Update the Case type to include:
```typescript
export interface Case {
  // ... existing fields ...
  emails: EmailMessage[];  // ADD THIS
}
```

---

### STEP 3: Update CaseDescriptionPanel Component

In `frontend/src/components/CaseDescriptionPanel.tsx`:

#### 3a. Import the EmailTimeline component at the top:
```typescript
import { EmailTimeline } from './EmailTimeline';
```

#### 3b. Add email timeline section in the render:

Find where you want to display it (maybe after the description section) and add:
```typescript
{/* Email Timeline */}
{caseData.emails && caseData.emails.length > 0 && (
  <div className="mt-4">
    <EmailTimeline emails={caseData.emails} />
  </div>
)}
```

---

## 🎯 Example Integration Location in CaseDescriptionPanel

After the existing description/content, add:

```typescript
export const CaseDescriptionPanel = ({ caseData, onDescriptionChange }) => {
  return (
    <div className="flex-1 overflow-y-auto">
      {/* Existing content... */}
      <div className="p-6">
        {/* Your existing description display */}
        
        {/* ADD EMAIL TIMELINE HERE */}
        <div className="mt-6">
          <h3 className="text-lg font-bold mb-3">Communication History</h3>
          <EmailTimeline emails={caseData.emails || []} />
        </div>
      </div>
    </div>
  );
};
```

---

## 🧪 Testing

### 1. Restart Backend Server
```bash
# Kill existing server
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Restart
cd backend && bash start.sh
```

### 2. Test with Multiple Emails

Send 2+ emails from the same address, then:
- Sync Gmail
- Navigate to the case
- You should see:
  - Email counter (1 / 3)
  - Arrow buttons to navigate
  - Dots showing current position
  - Quick jump buttons at bottom

---

## 📸 Expected UI

```
┌─────────────────────────────────────────┐
│ 📧 Email Timeline       (2 / 3)  ← →    │
├─────────────────────────────────────────┤
│ Subject: Follow-up on my CAF issue      │
│ 📧 john@email.com  📅 10 Jan 2026 14:30 │
├─────────────────────────────────────────┤
│                                         │
│ Hi,                                     │
│                                         │
│ I wanted to follow up on my housing     │
│ benefit appeal. Did you receive the     │
│ documents I sent last week?             │
│                                         │
│ Thank you.                              │
│                                         │
├─────────────────────────────────────────┤
│ Quick Jump:                             │
│ [Email 1] [Email 2*] [Email 3]         │
│ 5 Jan    10 Jan     15 Jan             │
└─────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Backend: No emails showing
- Check database: `python backend/scripts/inspect_db.py`
- Verify `queries` collection has `is_email: True` records
- Check `submission_id` matches case `_id`

### Frontend: Component not showing
- Check browser console for errors
- Verify `caseData.emails` has data
- Check import paths are correct

### Navigation not working
- Verify `emails` array has multiple items
- Check useState is updating correctly

---

## ✅ Completion Checklist

- [ ] Helper function added to `routes.py`
- [ ] `get_cases` updated to fetch emails
- [ ] `CaseResponse` includes emails field  
- [ ] `types.ts` updated with EmailMessage type
- [ ] EmailTimeline component imported
- [ ] EmailTimeline rendered in case view
- [ ] Backend server restarted
- [ ] Tested with multiple emails
- [ ] Navigation works (arrows + dots)

---

**Once complete, you'll have a fully functional email timeline that lets lawyers navigate through all client communications in chronological order!** 🚀
