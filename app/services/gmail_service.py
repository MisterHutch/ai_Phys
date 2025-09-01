import os
import base64
import json
from datetime import datetime
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import pickle

class GmailService:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
        self.credentials = None
        self.service = None
        self.credentials_file = 'gmail_credentials.json'
        self.token_file = 'gmail_token.pickle'
    
    def setup_oauth_flow(self, client_config: Dict) -> str:
        """Setup OAuth flow and return authorization URL"""
        try:
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # For installed apps
            )
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            # Store flow for later use
            with open('oauth_flow.pickle', 'wb') as f:
                pickle.dump(flow, f)
                
            return auth_url
            
        except Exception as e:
            raise Exception(f"Error setting up OAuth flow: {str(e)}")
    
    def complete_oauth_flow(self, authorization_code: str) -> bool:
        """Complete OAuth flow with authorization code"""
        try:
            # Load the flow
            with open('oauth_flow.pickle', 'rb') as f:
                flow = pickle.load(f)
            
            # Exchange code for token
            flow.fetch_token(code=authorization_code)
            
            # Save credentials
            self.credentials = flow.credentials
            self._save_credentials()
            
            # Initialize service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            return True
            
        except Exception as e:
            raise Exception(f"Error completing OAuth flow: {str(e)}")
    
    def _save_credentials(self):
        """Save credentials to file"""
        with open(self.token_file, 'wb') as token:
            pickle.dump(self.credentials, token)
    
    def _load_credentials(self) -> bool:
        """Load existing credentials"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
                
                # Check if credentials are expired and refresh if needed
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    self._save_credentials()
                
                if self.credentials and self.credentials.valid:
                    self.service = build('gmail', 'v1', credentials=self.credentials)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error loading credentials: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if not self.credentials:
            self._load_credentials()
        
        return self.credentials is not None and self.credentials.valid
    
    def get_user_profile(self) -> Optional[Dict]:
        """Get user's Gmail profile"""
        try:
            if not self.is_authenticated():
                return None
            
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'email': profile.get('emailAddress'),
                'total_messages': profile.get('messagesTotal', 0),
                'total_threads': profile.get('threadsTotal', 0)
            }
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def get_messages(self, query: str = '', max_results: int = 100) -> List[Dict]:
        """Get Gmail messages"""
        try:
            if not self.is_authenticated():
                return []
            
            # Get message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full message details
            detailed_messages = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Parse message data
                    parsed_msg = self._parse_message(message)
                    if parsed_msg:
                        detailed_messages.append(parsed_msg)
                        
                except Exception as e:
                    print(f"Error getting message {msg['id']}: {str(e)}")
                    continue
            
            return detailed_messages
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def _parse_message(self, message: Dict) -> Optional[Dict]:
        """Parse Gmail message data"""
        try:
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Get message body
            body_text = ''
            body_html = ''
            
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body_text = self._decode_message_body(part['body'].get('data', ''))
                    elif part['mimeType'] == 'text/html':
                        body_html = self._decode_message_body(part['body'].get('data', ''))
            else:
                if message['payload']['mimeType'] == 'text/plain':
                    body_text = self._decode_message_body(message['payload']['body'].get('data', ''))
                elif message['payload']['mimeType'] == 'text/html':
                    body_html = self._decode_message_body(message['payload']['body'].get('data', ''))
            
            # Parse date
            date_sent = None
            if 'Date' in header_dict:
                try:
                    from email.utils import parsedate_to_datetime
                    date_sent = parsedate_to_datetime(header_dict['Date'])
                except:
                    pass
            
            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': header_dict.get('Subject', ''),
                'sender_email': header_dict.get('From', ''),
                'sender_name': self._extract_name_from_email(header_dict.get('From', '')),
                'recipient_emails': header_dict.get('To', ''),
                'body_text': body_text,
                'body_html': body_html,
                'date_sent': date_sent.isoformat() if date_sent else None,
                'date_received': datetime.now().isoformat(),
                'labels': ','.join(message.get('labelIds', [])),
                'message_type': 'received' if 'SENT' not in message.get('labelIds', []) else 'sent'
            }
            
        except Exception as e:
            print(f"Error parsing message: {str(e)}")
            return None
    
    def _decode_message_body(self, encoded_body: str) -> str:
        """Decode base64url encoded message body"""
        try:
            if not encoded_body:
                return ''
            
            # Add padding if needed
            missing_padding = len(encoded_body) % 4
            if missing_padding:
                encoded_body += '=' * (4 - missing_padding)
            
            # Decode base64url
            decoded_bytes = base64.urlsafe_b64decode(encoded_body.encode('utf-8'))
            return decoded_bytes.decode('utf-8')
            
        except Exception as e:
            print(f"Error decoding message body: {str(e)}")
            return ''
    
    def _extract_name_from_email(self, email_field: str) -> str:
        """Extract name from email field"""
        try:
            if '<' in email_field and '>' in email_field:
                return email_field.split('<')[0].strip().strip('"')
            return email_field.split('@')[0] if '@' in email_field else email_field
        except:
            return email_field

# Global service instance
gmail_service = GmailService()