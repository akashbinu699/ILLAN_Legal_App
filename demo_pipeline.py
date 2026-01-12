import requests
import time
import json

def run_demo():
    BASE_URL = "http://localhost:8000/api"
    
    # 1. Simulate a client submission
    # In the new flow, this ONLY sends an email and DOES NOT save to DB
    print("\n--- 🟢 STEP 1: CLIENT SUBMISSION ---")
    client_data = {
        "email": "ilan.test.client@example.com",
        "phone": "07 12 34 56 78",
        "description": "Bonjour, je vous contacte car la CAF a réduit mes APL (Aide Personnalisée au Logement) de moitié sans explication. Je souhaite contester cette décision. Je suis actuellement en phase de conciliation (RAPO).",
        "files": [] # No files for simple demo
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/submit", json=client_data)
        resp.raise_for_status()
        submission = resp.json()
        case_id = submission['case_id']
        print(f"✅ Submission Received!")
        print(f"   CASE ID Generated: {case_id}")
        print(f"   Server Status: {submission['status']}")
        print(f"   Note: At this point, the case is NOT in the database yet. It's only in your Email.")
    except Exception as e:
        print(f"❌ Submission Failed: {e}")
        return

    # 2. Wait for the email to arrive (and for you to 'sync' it)
    print("\n--- ⏳ STEP 2: WAITING FOR EMAIL DELIVERY ---")
    print("   (Simulating the time it takes for the email to reach your inbox)")
    time.sleep(10)

    # 3. Trigger the Sync
    # This imitates the Webhook or the "Sync Gmail" button
    print("\n--- 🟢 STEP 3: SYNCING GMAIL & AI ANALYSIS ---")
    print(f"   Searching for emails containing: {case_id}")
    try:
        sync_resp = requests.post(f"{BASE_URL}/sync-gmail-case/{case_id}")
        sync_resp.raise_for_status()
        sync_info = sync_resp.json()
        print(f"✅ Sync Complete!")
        print(f"   Emails Found: {sync_info['synced_count']}")
        print(f"   New Case Created in DB: {sync_info['new_case_created']}")
    except Exception as e:
        print(f"❌ Sync Failed: {e}")
        return

    # 4. Verify the AI Results
    print("\n--- 🟢 STEP 4: VERIFYING AI DETECTION ---")
    try:
        # Get all cases to find our new one
        cases_resp = requests.get(f"{BASE_URL}/cases")
        cases_resp.raise_for_status()
        groups = cases_resp.json()
        
        target_case = None
        for group in groups:
            for case in group['cases']:
                if case['case_id'] == case_id:
                    target_case = case
                    break
        
        if target_case:
            print(f"✅ Case found in Dashboard!")
            print(f"   Detected Stage: {target_case['stage']}")
            print(f"   Detected Prestations: {[p['name'] for p in target_case['prestations']]}")
            print(f"   Status: {target_case['status']}")
            print("\n   🚀 PIPELINE SUCCESSFUL!")
        else:
            print("❌ Case not found in database. Sync might have failed to save.")
            
    except Exception as e:
        print(f"❌ Verification Failed: {e}")

if __name__ == "__main__":
    run_demo()
