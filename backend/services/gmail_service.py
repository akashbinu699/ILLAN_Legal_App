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
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send']

class GmailService:
    """Service for interacting with Gmail API."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        token_path = 'backend/token.json'
        credentials_path = 'backend/credentials.json'
        
        # Load existing token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If no valid credentials, use refresh token from env
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif settings.gmail_refresh_token:
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
            else:
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
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
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
        """Extract text from message payload."""
        body_text = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                body = part.get('body', {})
                data = body.get('data', '')
                
                if mime_type == 'text/plain' and data:
                    body_text += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            body = payload.get('body', {})
            data = body.get('data', '')
            if data:
                body_text = base64.urlsafe_b64decode(data).decode('utf-8')
        
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
        
        # Otherwise, try to extract key-value pairs
        form_data = {}
        lines = body_text.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                form_data[key.strip()] = value.strip()
        
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
                self.authenticate()
            except Exception as e:
                print(f"Failed to authenticate Gmail service: {e}")
                return False
        
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    filename = attachment.get('name', 'attachment')
                    mime_type = attachment.get('mimeType', 'application/octet-stream')
                    file_data = base64.b64decode(attachment.get('base64', ''))
                    
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
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Send message
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"Email sent successfully. Message ID: {send_message.get('id')}")
            return True
            
        except HttpError as error:
            print(f'An error occurred sending email: {error}')
            return False
        except Exception as e:
            print(f'Unexpected error sending email: {e}')
            return False

# Global instance
gmail_service = GmailService()

