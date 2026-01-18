from backend.services.gmail_service import gmail_service
import sys
import os

# Add path to enable imports
sys.path.append(os.getcwd())

def test_search():
    print("Testing Gmail Search...")
    query = '-label:ILAN_PROCESSED' 
    # Try broader query if 0? No let's stick to the sync query.
    
    msgs = gmail_service.get_messages(query, max_results=10)
    print(f"Query: '{query}'")
    print(f"Found {len(msgs)} messages.")
    
    if msgs:
        print(f"Sample ID: {msgs[0]['id']}")
    else:
        print("Debugging: Checking if checking INBOX works...")
        msgs_inbox = gmail_service.get_messages('in:inbox', max_results=5)
        print(f"INBOX has {len(msgs_inbox)} messages.")

if __name__ == "__main__":
    test_search()
