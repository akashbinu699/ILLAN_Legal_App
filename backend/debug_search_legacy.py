import sys
import os
from pathlib import Path

# Connect to project root for imports
current_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(current_dir))

from backend.services.gmail_service import gmail_service

def run_debug():
    print("Authenticating...")
    gmail_service.authenticate()
    
    # 1. Test exactly what is currently in the code
    q1 = '(subject:"NEW LEGAL CASE" OR subject:"New Case #") -label:ILAN_PROCESSED'
    
    # 2. Test broader, safer query (no hash, no quotes around hash)
    q2 = 'subject:"New Case"'
    
    # 3. Test just the legacy phrase
    q3 = 'subject:"New Case #"'
    
    queries = [
        ("Current Logic", q1),
        ("Broader 'New Case'", q2),
        ("Specific 'New Case #'", q3)
    ]
    
    print("\n--- STARTING SEARCH DIAGNOSTICS ---")
    for name, query in queries:
        print(f"\nTesting: {name}")
        print(f"Query: [{query}]")
        try:
            msgs = gmail_service.get_messages(query=query, max_results=5)
            print(f"Found: {len(msgs)} messages")
            for m in msgs:
                full = gmail_service.get_message(m['id'])
                payload = full.get('payload', {})
                headers = payload.get('headers', [])
                subj = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
                print(f" - Subject: {subj}")
                
                # Debug Parsing for Legacy Cases
                if "New Case #" in subj:
                    print("   [DEBUG] Inspecting Legacy Parsing...")
                    content = gmail_service.parse_message_content(full)
                    print(f"   [DEBUG] Parsed Data: {content.get('form_data')}")
                    print(f"   [DEBUG] Body Snippet: {content.get('body')}")
        except Exception as e:
            print(f"Error: {e}")
            
    print("\n--- DIAGNOSTICS COMPLETE ---")

if __name__ == "__main__":
    run_debug()
