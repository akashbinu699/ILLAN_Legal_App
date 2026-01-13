import requests
import json

def check_api():
    try:
        print("Fetching /api/cases...")
        r = requests.get('http://localhost:8000/api/cases')
        if r.status_code != 200:
            print(f"Error: {r.status_code}")
            return
            
        data = r.json()
        print(f"Total Cases: {len(data)}")
        
        if len(data) > 0:
            print(f"Sample Keys: {data[0].keys()}")
            print(f"Sample Data: {data[0]}")
            
        for group in data:
            for c in group.get('cases'):
                # Try getting with 'case_id'
                cid = c.get('case_id')
                desc = c.get('description', '')
                if desc:
                     preview = desc[:50].replace('\n', ' ')
                else:
                     preview = "EMPTY"
                
                print(f"ID: {cid} | Desc: {preview}...")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_api()
