import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.mongo import get_database, MongoDB

async def check_db():
    print("Checking Database...")
    await MongoDB.connect_db()
    db = MongoDB.db
    
    msg_id = "19bb2f522032197f"
    
    # Check Queries
    query = await db.queries.find_one({"gmail_message_id": msg_id})
    if query:
        print(f"✅ Found Query/Email in DB! ID: {query['_id']}")
        print(f"   Linked to Submission ID: {query.get('submission_id')}")
    else:
        print("❌ Message NOT found in Queries collection.")
        
    # Check Submissions
    case_id = "CAS_12-01-26_16:06:07"
    sub = await db.submissions.find_one({"case_id": case_id})
    if sub:
        print(f"✅ Found Submission in DB! ID: {sub['_id']}")
        print(f"   Email: {sub['email']}")
        print(f"   Status: {sub['status']}")
    else:
        print("❌ Submission NOT found in DB.")

    await MongoDB.close_db()

if __name__ == "__main__":
    asyncio.run(check_db())
