import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

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
    
    print("\nRESETTING GMAIL LABELS:")
    try:
        from backend.services.gmail_service import gmail_service
        # Authenticate if needed
        if not gmail_service.service:
            gmail_service.authenticate()
            
        print("Searching for processed emails...")
        # Get label ID
        results = gmail_service.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        label_id = next((l['id'] for l in labels if l['name'] == "ILAN_PROCESSED"), None)
        
        if label_id:
            # Loop to find ALL messages
            while True:
                response = gmail_service.service.users().messages().list(
                    userId='me', 
                    q='label:ILAN_PROCESSED',
                    maxResults=500
                ).execute()
                
                messages = response.get('messages', [])
                if not messages:
                    break
                    
                print(f"Found {len(messages)} processed emails. Removing label...")
                
                # Batch modify only allows 1000 IDs, but here we process page by page
                batch = {
                    'ids': [msg['id'] for msg in messages],
                    'removeLabelIds': [label_id]
                }
                gmail_service.service.users().messages().batchModify(
                    userId='me',
                    body=batch
                ).execute()
                print(f"✅ Removed label from batch of {len(messages)}.")
            
            print("✅ 'ILAN_PROCESSED' label removed from all messages.")

        else:
            print("Label 'ILAN_PROCESSED' not found.")
            
    except Exception as e:
        print(f"⚠️ Error resetting Gmail labels: {e}")

    print("\n✅ System Reset Complete.")
    print("Next Step: Click 'Sync Gmail' in the app to re-import emails and save PDFs.")
    
    await MongoDB.close_db()

if __name__ == "__main__":
    asyncio.run(clear_db())
