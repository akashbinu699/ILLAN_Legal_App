"""Gmail API service for collecting form submissions."""
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from backend.config import settings
import os
import json

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 
          'https://www.googleapis.com/auth/gmail.send']

class GmailService:
    """Service for interacting with Gmail API."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Use absolute paths relative to project root
        from backend.config import PROJECT_ROOT
        token_path = os.path.join(PROJECT_ROOT, 'backend', 'token.json')
        credentials_path = os.path.join(PROJECT_ROOT, 'backend', 'credentials.json')
        
        # Load existing token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If no valid credentials, use refresh token from env
        # If no valid credentials, use refresh token from env
        if not creds or not creds.valid:
            refreshed = False
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    refreshed = True
                except Exception as e:
                    print(f"Failed to refresh existing token: {e}")

            if not refreshed and settings.gmail_refresh_token:
                try:
                    # Use refresh token from environment
                    creds = Credentials(
                        token=None,
                        refresh_token=settings.gmail_refresh_token,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=settings.gmail_client_id,
                        client_secret=settings.gmail_client_secret,
                        scopes=SCOPES
                    )
                    creds.refresh(Request())
                    refreshed = True
                except Exception as e:
                    print(f"Failed to refresh env token: {e}")
            
            if not refreshed:
                # Interactive OAuth flow
                if os.path.exists(credentials_path):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    raise ValueError(
                        "Gmail credentials not found. Please set GMAIL_REFRESH_TOKEN "
                        "in .env or provide credentials.json"
                    )
            
            # Save credentials for next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def get_messages(self, query: str = "", max_results: int = 10) -> List[Dict]:
        """Get messages matching query."""
        if not self.service:
            self.authenticate()
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return messages
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def get_message(self, msg_id: str) -> Optional[Dict]:
        """Get full message details."""
        if not self.service:
            self.authenticate()
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            return message
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
            
    def ensure_label_exists(self, label_name: str) -> str:
        """Check if label exists by name, create it if it doesn't. Returns label ID."""
        if not self.service:
            self.authenticate()
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    return label['id']
            
            # Create label
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = self.service.users().labels().create(userId='me', body=label_object).execute()
            print(f"[GMAIL] Created new label: {label_name}")
            return created_label['id']
        except Exception as e:
            print(f"[GMAIL] Error ensuring label exists: {e}")
            return ""

    def add_label_to_message(self, msg_id: str, label_name: str):
        """Add a label to a specific message."""
        if not self.service:
            self.authenticate()
        try:
            label_id = self.ensure_label_exists(label_name)
            if not label_id: return
            
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': [msg_id],
                    'addLabelIds': [label_id]
                }
            ).execute()
            print(f"[GMAIL] Applied label '{label_name}' to message {msg_id}")
        except Exception as e:
            print(f"[GMAIL] Error adding label to message: {e}")

    def remove_label_from_message(self, msg_id: str, label_name: str):
        """Remove a label from a specific message."""
        if not self.service:
            self.authenticate()
        try:
            # Need to find ID for the name
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            label_id = next((l['id'] for l in labels if l['name'].lower() == label_name.lower()), None)
            
            if not label_id: return
            
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': [msg_id],
                    'removeLabelIds': [label_id]
                }
            ).execute()
            print(f"[GMAIL] Removed label '{label_name}' from message {msg_id}")
        except Exception as e:
            print(f"[GMAIL] Error removing label: {e}")
    
    def extract_attachments(self, message: Dict) -> List[Dict]:
        """Extract attachments from message."""
        attachments = []
        
        payload = message.get('payload', {})
        parts = payload.get('parts', [])
        
        for part in parts:
            filename = part.get('filename')
            body = part.get('body', {})
            attachment_id = body.get('attachmentId')
            
            if attachment_id and filename:
                # Download attachment
                attachment = self.service.users().messages().attachments().get(
                    userId='me',
                    messageId=message['id'],
                    id=attachment_id
                ).execute()
                
                file_data = base64.urlsafe_b64decode(
                    attachment['data'].encode('UTF-8')
                )
                
                # Determine MIME type
                mime_type = part.get('mimeType', 'application/octet-stream')
                
                attachments.append({
                    'filename': filename,
                    'mime_type': mime_type,
                    'data': file_data,
                    'base64': base64.b64encode(file_data).decode('utf-8')
                })
        
        return attachments
    
    def parse_message_content(self, message: Dict) -> Dict:
        """Parse message content to extract form data."""
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers (case-insensitive)
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        
        # Extract body
        body_text = self._extract_body_text(payload)
        
        # Try to parse form data from body
        # Assuming form data is in JSON format or structured text
        form_data = self._parse_form_data(body_text)
        
        return {
            'subject': subject,
            'from': from_email,
            'date': date,
            'body': body_text,
            'form_data': form_data
        }
    
    def _extract_body_text(self, payload: Dict) -> str:
        """Extract text from message payload, preferring plain text but falling back to HTML."""
        body_text = ""
        html_text = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                body = part.get('body', {})
                data = body.get('data', '')
                
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                    if mime_type == 'text/plain':
                        body_text += decoded
                    elif mime_type == 'text/html':
                        html_text += decoded
        else:
            body = payload.get('body', {})
            data = body.get('data', '')
            mime_type = payload.get('mimeType', '')
            
            if data:
                decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                if mime_type == 'text/plain':
                    body_text = decoded
                elif mime_type == 'text/html':
                    html_text = decoded
        
        # Prefer plain text, fall back to stripped HTML
        if not body_text and html_text:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_text, 'html.parser')
                body_text = soup.get_text('\n')
            except ImportError:
                # Fallback if bs4 not available (though it should be)
                import re
                body_text = re.sub('<[^<]+?>', '', html_text)
                
        return body_text
    
    def _parse_form_data(self, body_text: str) -> Dict:
        """Parse form data from email body."""
        # Try to extract JSON if present
        import re
        json_match = re.search(r'\{.*\}', body_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Otherwise, extract key-value pairs, handling multi-line descriptions
        form_data = {}
        
        # Standard fields (New Format)
        patterns_new = {
            'CASE ID': r'CASE ID:\s*(CAS_[\d\-_:]+)',
            'CLIENT EMAIL': r'CLIENT EMAIL:\s*([^\n\r]+)',
            'PHONE': r'PHONE:\s*([^\n\r]*)',
            'DESCRIPTION': r'DESCRIPTION:\s*(.*?)(?=\s*\n\s*\d+\s*document\(s\) attached|$)'
        }
        
        # Legacy fields (Old Format)
        # Example: Email(esmeraldaavsar@yahoo.fr);
        # Using \s* to handle potential non-breaking spaces or formatting spacing
        patterns_legacy = {
            'CASE ID': r'CaseNo\s*\(\s*(.*?)\s*\)', 
            'CLIENT EMAIL': r'Email\s*\(\s*(.*?)\s*\)',
            'PHONE': r'Telephone\s*\(\s*(.*?)\s*\)',
            'DESCRIPTION': r'Context\s*\(\s*(.*?)\s*\);',
            'CASE DATE': r'CaseDate\s*\(\s*(.*?)\s*\)',
            'CASE TIME': r'CaseTime\s*\(\s*(.*?)\s*\)'
        }

        # Try new format first
        for key, pattern in patterns_new.items():
            match = re.search(pattern, body_text, re.DOTALL | re.IGNORECASE)
            if match:
                form_data[key] = match.group(1).strip()
                
        # If no CASE ID found, try legacy format
        if 'CASE ID' not in form_data:
            for key, pattern in patterns_legacy.items():
                match = re.search(pattern, body_text, re.DOTALL | re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    # Clean up trailing parens if regex got greedy (though non-greedy .*? should handle it)
                    if val.endswith(')'): val = val[:-1] 
                    form_data[key] = val
            
            # If we found a legacy Case ID (e.g. "313"), normalize it to CAS_ format if needed?
            # Or just keep it as is. Route logic expects CAS_ prefix usually for date-based ones, 
            # but let's see. If it's just "313", the routes might accept it. 
            # However, routes.py line 250 logic expects to generate a CAS_ ID if missing.
            # If we extract "313", we should probably prefix it to match system.
            if 'CASE ID' in form_data and not form_data['CASE ID'].startswith('CAS_'):
                 # Ensure it looks like a case ID our system likes, or just keep it.
                 # Let's prefix it to be safe and consistent with "CAS_" check in sync_all_gmail
                 # content['subject'] check looks for "CAS_" but we updated the subject query to allow "New Case #"
                 # So we are good.
                 pass
        
        return form_data
    
    def send_email_with_attachments(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: List[Dict] = None
    ) -> bool:
        """
        Send an email with attachments via Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: List of dicts with 'name', 'mimeType', and 'base64' keys
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.service:
            try:
                print("[GMAIL] Authenticating Gmail service...")
                self.authenticate()
                print("[GMAIL] Authentication successful")
            except Exception as e:
                print(f"[GMAIL] ERROR: Failed to authenticate Gmail service: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        try:
            print(f"[GMAIL] Creating email message to {to_email}")
            # Create message
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            # Get sender email from Gmail profile
            try:
                profile = self.service.users().getProfile(userId='me').execute()
                sender_email = profile.get('emailAddress', 'me')
                message['from'] = sender_email
                print(f"[GMAIL] Sender email: {sender_email}")
            except Exception as e:
                print(f"[GMAIL] WARNING: Could not get sender email from profile: {e}")
                # Gmail API will use the authenticated user's email by default
                message['from'] = 'me'
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            print(f"[GMAIL] Email body attached ({len(body)} chars)")
            
            # Add attachments
            if attachments:
                print(f"[GMAIL] Processing {len(attachments)} attachment(s)...")
                for idx, attachment in enumerate(attachments):
                    filename = attachment.get('name', 'attachment')
                    mime_type = attachment.get('mimeType', 'application/octet-stream')
                    base64_data = attachment.get('base64', '')
                    
                    if not base64_data:
                        print(f"[GMAIL] WARNING: Attachment {idx+1} ({filename}) has no base64 data, skipping")
                        continue
                    
                    try:
                        file_data = base64.b64decode(base64_data)
                        print(f"[GMAIL] Decoded attachment {idx+1}: {filename} ({len(file_data)} bytes, {mime_type})")
                        
                        # Create MIME part
                        part = MIMEBase(*mime_type.split('/', 1))
                        part.set_payload(file_data)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        
                        # Encode in base64
                        email.encoders.encode_base64(part)
                        message.attach(part)
                        print(f"[GMAIL] Attachment {idx+1} attached successfully")
                    except Exception as e:
                        print(f"[GMAIL] ERROR: Failed to process attachment {idx+1} ({filename}): {e}")
                        continue
            else:
                print("[GMAIL] No attachments to process")
            
            # Encode message
            print("[GMAIL] Encoding message...")
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            print(f"[GMAIL] Message encoded ({len(raw_message)} chars)")
            
            # Send message
            print("[GMAIL] Sending message via Gmail API...")
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = send_message.get('id')
            print(f"[GMAIL] SUCCESS: Email sent successfully. Message ID: {message_id}")
            return True
            
        except HttpError as error:
            print(f'[GMAIL] ERROR: HttpError occurred sending email: {error}')
            print(f'[GMAIL] Error details: {error.error_details if hasattr(error, "error_details") else "N/A"}')
            print(f'[GMAIL] Error status: {error.resp.status if hasattr(error, "resp") else "N/A"}')
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f'[GMAIL] ERROR: Unexpected error sending email: {e}')
            import traceback
            traceback.print_exc()
            return False

# Global instance
gmail_service = GmailService()

