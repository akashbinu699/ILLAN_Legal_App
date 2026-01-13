"""Script to get Gmail API refresh token."""
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send']

def main():
    credentials_path = 'backend/credentials.json'
    
    if not os.path.exists(credentials_path):
        print("ERROR: credentials.json not found!")
        print(f"Please download it from Google Cloud Console and save it to {credentials_path}")
        return
    
    print("Starting OAuth flow...")
    print("A browser window will open. Please sign in and authorize the app.")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Extract values
    refresh_token = creds.refresh_token
    
    # Read credentials.json to get client ID and secret
    with open(credentials_path, 'r') as f:
        creds_data = json.load(f)
        client_data = creds_data.get('installed') or creds_data.get('web')
        client_id = client_data['client_id']
        client_secret = client_data['client_secret']
    
    print("\n" + "="*60)
    print("✅ SUCCESS! Add these to your .env file:")
    print("="*60)
    print(f"GMAIL_CLIENT_ID={client_id}")
    print(f"GMAIL_CLIENT_SECRET={client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={refresh_token}")
    print("="*60)
    print("\n⚠️  Keep these credentials secure and never commit them to git!")

if __name__ == '__main__':
    main()
