
import asyncio
import os
import sys

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.db import get_database
from backend.services.simplified_sync import process_gmail_sync_simplified

async def run_manual_sync():
    print("Initializing Manual Sync...")
    db = await get_database()
    
    print("Running process_gmail_sync_simplified...")
    result = await process_gmail_sync_simplified(days=30, db=db)
    print("Sync Result:", result)

if __name__ == "__main__":
    asyncio.run(run_manual_sync())
