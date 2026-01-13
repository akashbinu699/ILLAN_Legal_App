from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send']

flow = InstalledAppFlow.from_client_secrets_file(
    'backend/credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

# Extract the refresh token
refresh_token = creds.refresh_token
print(f"Refresh Token: {refresh_token}")

# Also extract client ID and secret from credentials.json
with open('backend/credentials.json', 'r') as f:
    creds_data = json.load(f)
    client_id = creds_data['installed']['client_id']
    client_secret = creds_data['installed']['client_secret']
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret}")

