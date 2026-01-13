import sys
import os
from pathlib import Path
import asyncio

# Connect to project root for imports
current_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(current_dir))

from backend.database.mongo import MongoDB

async def check_descriptions():
    try:
        await MongoDB.connect_db()
        db = MongoDB.db
        print("--- CHECKING CASE DESCRIPTIONS IN DB ---")
        
        # Aggregate by case_id to see effective description
        pipeline = [
            {"$group": {
                "_id": "$case_id",
                "description": {"$first": "$description"},
                "count": {"$sum": 1}
            }}
        ]
        
        async for doc in db.submissions.aggregate(pipeline):
            desc = doc.get('description', '')
            preview = desc[:50].replace('\n', ' ') if desc else "EMPTY"
            print(f"Case: {doc['_id']} (Docs: {doc['count']}) -> {preview}...")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await MongoDB.close_db()

if __name__ == "__main__":
    asyncio.run(check_descriptions())
