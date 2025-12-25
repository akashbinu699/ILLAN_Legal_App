#!/usr/bin/env python3
"""Script to reset the database and clear all submissions."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.db import AsyncSessionLocal, engine
from backend.database.models import Submission, Document, Chunk, Query
from sqlalchemy import text

async def reset_database():
    """Clear all data from the database."""
    print("=" * 60)
    print("DATABASE RESET SCRIPT")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Count existing records
            result = await db.execute(text("SELECT COUNT(*) FROM submissions"))
            count = result.scalar()
            print(f"Found {count} existing submissions")
            
            if count == 0:
                print("Database is already empty.")
                return
            
            # Confirm deletion
            print("\n⚠️  WARNING: This will delete ALL data from the database!")
            print("This includes:")
            print("  - All submissions")
            print("  - All documents")
            print("  - All chunks")
            print("  - All queries")
            print("\nType 'RESET' to confirm: ", end='')
            
            confirmation = input().strip()
            if confirmation != 'RESET':
                print("Reset cancelled.")
                return
            
            # Delete all records (in correct order due to foreign keys)
            print("\nDeleting records...")
            
            # Delete chunks first (has foreign key to documents)
            await db.execute(text("DELETE FROM chunks"))
            print("  ✓ Deleted chunks")
            
            # Delete documents (has foreign key to submissions)
            await db.execute(text("DELETE FROM documents"))
            print("  ✓ Deleted documents")
            
            # Delete queries (has foreign key to submissions)
            await db.execute(text("DELETE FROM queries"))
            print("  ✓ Deleted queries")
            
            # Delete submissions
            await db.execute(text("DELETE FROM submissions"))
            print("  ✓ Deleted submissions")
            
            # Commit changes
            await db.commit()
            
            print("\n✅ Database reset complete!")
            print("All data has been cleared. CAS numbers will start from 1 for new submissions.")
            
        except Exception as e:
            print(f"\n❌ Error resetting database: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(reset_database())

