import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.mongo import get_database, MongoDB

async def clear_db():
    print("=" * 60)
    print("CLEARING DATABASE (Removing all Test Data)")
    print("=" * 60)
    
    await MongoDB.connect_db()
    db = MongoDB.db
    
    if db is None:
        print("❌ Failed to connect to database.")
        return

    # Count before deletion
    sub_count = await db.submissions.count_documents({})
    query_count = await db.queries.count_documents({})
    
    print(f"Found {sub_count} submissions and {query_count} queries/emails.")
    
    # Delete All
    await db.submissions.delete_many({})
    await db.queries.delete_many({})
    
    print("🗑️  Deleted all data.")
    print("\n✅ Database is now EMPTY.")
    print("Next Step: Click 'Sync Gmail' in the app to import ONLY real emails.")
    
    await MongoDB.close_db()

if __name__ == "__main__":
    asyncio.run(clear_db())
