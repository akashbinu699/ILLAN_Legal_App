import asyncio
import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.gmail_service import gmail_service

async def debug_search():
    print("=" * 60)
    print("DEBUGGING GMAIL SEARCH")
    print("=" * 60)
    
    # 1. Authenticate
    print("Authenticating...")
    gmail_service.authenticate()
    print("Authentication successful.")
    
    # 2. Define the exact Case ID from the logs
    case_id = "CAS_12-01-26_16:06:07"
    
    # 3. Search specifically for this ID
    query = f'"{case_id}"'
    print(f"\nSearching for query: {query}")
    
    messages = gmail_service.get_messages(query=query, max_results=10)
    
    print(f"\nFound {len(messages)} messages.")
    
    if len(messages) == 0:
        print("❌ Gmail API returned NO results for this Case ID.")
        print("Possible reasons:")
        print(" - The email hasn't indexed yet (wait a minute)")
        print(" - The email went to Spam")
        print(" - The email was not actually sent/received")
    else:
        print("✅ Success! Found messages:")
        for msg in messages:
            print(f" - ID: {msg['id']} (Thread: {msg['threadId']})")
            
            # Get details
            full_msg = gmail_service.get_message(msg['id'])
            if full_msg:
                headers = full_msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                print(f"   Subject: {subject}")

if __name__ == "__main__":
    asyncio.run(debug_search())
