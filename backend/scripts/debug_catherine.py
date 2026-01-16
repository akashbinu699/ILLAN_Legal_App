
import asyncio
import os
import sys
from bson import ObjectId

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.db import get_database

async def debug_catherine():
    db = await get_database()
    target_email = "catherine.go@laposte.net"
    
    print(f"--- DEBUGGING {target_email} ---")
    
    # 1. Find Submissions
    subs = await db.submissions.find({"email": target_email}).to_list(None)
    print(f"\n1. Found {len(subs)} Submissions (Cases):")
    for sub in subs:
        print(f"   - ID: {sub['_id']}")
        print(f"   - CaseID: {sub.get('case_id')}")
        print(f"   - SubmittedAt: {sub.get('submitted_at')}")
    
    if not subs:
        print("   (No submissions found!)")
        return

    primary_sub_id = subs[0]["_id"]

    # 2. Find Emails by Address
    emails_by_addr = await db.queries.find({"from_email": target_email}).to_list(None)
    print(f"\n2. Found {len(emails_by_addr)} Emails/Queries from address:")
    for email in emails_by_addr:
        print(f"   - Email ID: {email['_id']}")
        print(f"   - Linked Submission ID: {email.get('submission_id')}")
        print(f"   - Subject: {email.get('query_text', '')[:50]}...")
        
        # Check mismatch
        if str(email.get('submission_id')) != str(primary_sub_id):
            print(f"     ⚠️ MISMATCH! Does not match primary Submission ID {primary_sub_id}")
        else:
            print("     ✅ Matches primary Submission ID")

if __name__ == "__main__":
    asyncio.run(debug_catherine())
