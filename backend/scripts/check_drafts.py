
import asyncio
import os
import sys

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.db import get_database

async def check_drafts():
    db = await get_database()
    print("--- CHECKING FOR SAVED DRAFTS ---")
    
    # Count total submissions
    total = await db.submissions.count_documents({})
    print(f"Total Cases: {total}")
    
    # Count drafts
    email_drafts = await db.submissions.count_documents({"generated_email_draft": {"$ne": None, "$ne": ""}})
    appeal_drafts = await db.submissions.count_documents({"generated_appeal_draft": {"$ne": None, "$ne": ""}})
    
    print(f"Cases with Email Drafts: {email_drafts}")
    print(f"Cases with Appeal/Letter Drafts: {appeal_drafts}")
    
    if email_drafts > 0:
        example = await db.submissions.find_one({"generated_email_draft": {"$ne": None}})
        print(f"\nExample Draft for {example.get('case_id')}:")
        print(f"Email Draft Length: {len(example.get('generated_email_draft', ''))} chars")
        print(f"Stored in field: 'generated_email_draft'")

if __name__ == "__main__":
    asyncio.run(check_drafts())
