import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.mongo import get_database, MongoDB

async def inspect_db():
    print("INSPECTING DB...")
    await MongoDB.connect_db()
    db = MongoDB.db
    
    cursor = db.submissions.find({})
    subs = await cursor.to_list(length=100)
    
    print(f"Found {len(subs)} submissions.")
    for sub in subs:
        print("-" * 40)
        print(f"ID: {sub['_id']}")
        print(f"Case ID: {sub['case_id']}")
        print(f"Email: '{sub['email']}'")
        print(f"Doc: {sub.get('document', {}).get('filename')}")
        print(f"Stage: {sub.get('stage')}")
        print(f"Benefits: {sub.get('prestations_detected')}")
        print(f"Description start: {sub['description'][:50]}...")
        if 'secretaire' in sub['email']:
            print("⚠️  BAD RECORD DETECTED!")
            
    await MongoDB.close_db()

if __name__ == "__main__":
    asyncio.run(inspect_db())
