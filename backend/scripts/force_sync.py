import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.db import get_db, MongoDB
# Mocking dependency
async def run_sync():
    print("Connecting to DB...")
    await MongoDB.connect_db()
    db = MongoDB.db
    
    # We need to import the function. 
    # Since sync_all_gmail relies on Depends(get_db), we can't call it directly easily without mocking or modification.
    # But we can replicate its logic or use the service directly if it was separated.
    # Actually, routes.py has the logic. Let's import it and try to call it with the db instance directly.
    
    from backend.api.routes import sync_all_gmail
    
    print("Calling sync_all_gmail...")
    try:
        # The route expects 'db' relative to Depends. We pass it explicitly.
        result = await sync_all_gmail(days=7, db=db)
        print("Sync Result:", result)
    except Exception as e:
        print("Sync Error:", e)
        import traceback
        traceback.print_exc()
    
    await MongoDB.close_db()

if __name__ == "__main__":
    asyncio.run(run_sync())
