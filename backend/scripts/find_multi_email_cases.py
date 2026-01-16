
import asyncio
import os
import sys
from collections import defaultdict

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.db import get_database

async def find_multi_email_cases():
    print("Connecting to MongoDB...")
    db = await get_database()
    
    print("Analyzing email history...")
    
    # 1. Get all email queries
    cursor = db.queries.find({"is_email": True})
    emails = await cursor.to_list(length=None)
    
    # 2. Group by submission_id (case)
    case_email_counts = defaultdict(int)
    for email in emails:
        sub_id = str(email.get('submission_id'))
        case_email_counts[sub_id] += 1
    
    # 3. Find cases with > 1 email
    multi_email_cases = {k: v for k, v in case_email_counts.items() if v > 1}
    
    if not multi_email_cases:
        print("\nNo cases found with multiple emails yet.")
        print("Note: You cleared the database recently. You may need to:")
        print("1. Send a second email from a test account")
        print("2. Click 'Sync Gmail' again")
        return

    print(f"\nFound {len(multi_email_cases)} cases with multiple emails:\n")
    print(f"{'CASE ID':<40} | {'EMAIL':<30} | {'COUNT':<10}")
    print("-" * 90)
    
    # 4. Fetch case details for display
    for sub_id, count in multi_email_cases.items():
        try:
            from bson import ObjectId
            sub = await db.submissions.find_one({"_id": ObjectId(sub_id)})
            if sub:
                case_id = sub.get('case_id', 'Unknown')
                user_email = sub.get('email', 'Unknown')
                print(f"{case_id:<40} | {user_email:<30} | {count:<10}")
        except Exception as e:
            print(f"Error fetching case {sub_id}: {e}")

if __name__ == "__main__":
    asyncio.run(find_multi_email_cases())
