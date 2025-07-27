"""
Email Collector Component

Handles Gmail API authentication and fetches job description emails.
"""

import os
import base64
import re
import json
from typing import Any, Optional, List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta

from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from google.oauth2.credentials import Credentials  # type: ignore

from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Constants for email filtering
ALLOWED_DOMAINS = [
    'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
    'careerbuilder.com', 'ziprecruiter.com', 'simplyhired.com',
    'dice.com', 'angel.co', 'stackoverflow.com', 'github.com',
    'lever.co', 'greenhouse.io', 'workday.com', 'bamboohr.com'
]

JOB_KEYWORDS = [
    'job description', 'position description', 'role description',
    'we are hiring', 'join our team', 'career opportunity',
    'open position', 'job opening', 'hiring for', 'apply now',
    'job posting', 'career opening', 'employment opportunity'
]

JD_ATTACHMENT_PATTERN = re.compile(
    r'\.(pdf|doc|docx|txt)$', re.IGNORECASE
)


class EmailCollector:
    """Handles Gmail API authentication and email collection."""
    
    def __init__(self, config: Config):
        self.config = config
        self.service: Any = None
        self.credentials: Optional[Credentials] = None
    
    def _authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth 2.0."""
        try:
            # Try to load existing credentials from token.json
            token_path = "data/token.json"
            if os.path.exists(token_path):
                with open(token_path, 'r') as token_file:
                    token_data = json.load(token_file)
                    self.credentials = Credentials.from_authorized_user_info(token_data)
            
            # If no valid credentials, try refresh token from config
            if not self.credentials or not self.credentials.valid:
                if self.config.GMAIL_REFRESH_TOKEN:
                    self.credentials = Credentials(
                        None,  # No access token initially
                        refresh_token=self.config.GMAIL_REFRESH_TOKEN,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id="your-client-id",  # This should be from credentials.json
                        client_secret="your-client-secret"  # This should be from credentials.json
                    )
                
                # If still no valid credentials, run OAuth flow
                if not self.credentials or not self.credentials.valid:
                    self._print_oauth_instructions()
                    self.credentials = self._get_oauth_credentials()
                
                # Save new credentials
                if self.credentials:
                    os.makedirs("data", exist_ok=True)
                    with open(token_path, 'w') as token_file:
                        token_data = {
                            'token': self.credentials.token,
                            'refresh_token': self.credentials.refresh_token,
                            'token_uri': self.credentials.token_uri,
                            'client_id': self.credentials.client_id,
                            'client_secret': self.credentials.client_secret,
                            'scopes': self.credentials.scopes
                        }
                        json.dump(token_data, token_file)
            
            # Build the Gmail service
            if self.credentials and self.credentials.valid:
                self.service = build('gmail', 'v1', credentials=self.credentials)
                logger.info("Gmail API authentication successful")
            else:
                raise Exception("Failed to obtain valid credentials")
                
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            raise
    
    def _print_oauth_instructions(self) -> None:
        """Print OAuth setup instructions."""
        print("\n" + "="*60)
        print("GMAIL API SETUP REQUIRED")
        print("="*60)
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download credentials.json and place it in the project root")
        print("6. Add your email as a test user in OAuth consent screen")
        print("7. Run this script again")
        print("="*60)
    
    def _get_oauth_credentials(self) -> Optional[Credentials]:
        """Get OAuth credentials through interactive flow."""
        try:
            credentials_path = "credentials.json"
            if not os.path.exists(credentials_path):
                print(f"Error: {credentials_path} not found!")
                print("Please download your OAuth credentials from Google Cloud Console")
                return None
            
            # Define the scopes
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
            
            # Run the OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            
            # This will open a browser window for authentication
            credentials = flow.run_local_server(port=0)
            
            return credentials
            
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return None
    
    def fetch_job_description_threads(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch email threads that might contain job descriptions.
        
        Args:
            max_results: Maximum number of threads to fetch
            
        Returns:
            List of email thread data
        """
        if not self.service:
            self._authenticate()
        
        try:
            # Build enhanced search query
            search_query = self._build_enhanced_search_query()
            
            # Fetch threads
            results = self.service.users().threads().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()
            
            threads = results.get('threads', [])
            thread_data = []
            
            for thread in threads:
                thread_id = thread['id']
                
                # Get detailed thread information
                thread_detail = self.service.users().threads().get(
                    userId='me', id=thread_id
                ).execute()
                
                messages = thread_detail.get('messages', [])
                if messages:
                    # Process the first message (most recent)
                    message = messages[0]
                    message_data = self._process_message(message)
                    
                    if message_data:
                        thread_data.append({
                            'thread_id': thread_id,
                            'message_count': len(messages),
                            'message': message_data
                        })
            
            logger.info(f"Found {len(thread_data)} potential job description threads")
            return thread_data
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Error fetching email threads: {e}")
            return []
    
    def _build_enhanced_search_query(self) -> str:
        """Build a comprehensive search query for job description emails."""
        query_parts = []
        
        # Domain-based search
        domain_queries = [f"from:{domain}" for domain in ALLOWED_DOMAINS]
        query_parts.append(f"({' OR '.join(domain_queries)})")
        
        # Keyword-based search
        keyword_queries = [f'"{keyword}"' for keyword in JOB_KEYWORDS]
        query_parts.append(f"({' OR '.join(keyword_queries)})")
        
        # Attachment search
        query_parts.append("has:attachment")
        
        # Time-based search (last 30 days)
        query_parts.append("newer_than:30d")
        
        # Combine all parts
        return " AND ".join(query_parts)
    
    def _process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a Gmail message and extract relevant information."""
        try:
            headers = message.get('payload', {}).get('headers', [])
            
            # Extract basic headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Check if this message is likely a job description
            if not self._is_likely_job_description(subject, sender):
                return None
            
            # Extract body content
            body = self._extract_message_body(message)
            
            # Extract attachments
            attachments = self._extract_attachments(message)
            
            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'attachments': attachments,
                'snippet': message.get('snippet', '')
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    def _is_likely_job_description(self, subject: str, sender: str) -> bool:
        """Check if an email is likely to contain a job description."""
        subject_lower = subject.lower()
        sender_lower = sender.lower()
        
        # Check domain match
        if self._check_domain_match(sender_lower):
            return True
        
        # Check keyword match in subject
        if self._check_keyword_hit(subject_lower):
            return True
        
        # Check for job-related patterns in sender
        job_patterns = ['recruiter', 'hiring', 'talent', 'careers', 'hr@']
        for pattern in job_patterns:
            if pattern in sender_lower:
                return True
        
        return False
    
    def _check_domain_match(self, sender: str) -> bool:
        """Check if sender domain is in allowed domains."""
        for domain in ALLOWED_DOMAINS:
            if domain in sender:
                return True
        return False
    
    def _check_keyword_hit(self, text: str) -> bool:
        """Check if text contains job-related keywords with word boundaries."""
        for keyword in JOB_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text.lower()):
                return True
        return False
    
    def _check_attachment_hit(self, filename: str) -> bool:
        """Check if attachment filename suggests job description."""
        return bool(JD_ATTACHMENT_PATTERN.search(filename))
    
    def _extract_message_body(self, message: Dict[str, Any]) -> str:
        """Extract text body from a Gmail message."""
        try:
            payload = message.get('payload', {})
            
            # Handle multipart messages
            if payload.get('mimeType') == 'multipart/alternative':
                parts = payload.get('parts', [])
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        return self._decode_body(part.get('body', {}))
                return ""
            
            # Handle simple text messages
            elif payload.get('mimeType') == 'text/plain':
                return self._decode_body(payload.get('body', {}))
            
            # Handle multipart/mixed messages
            elif payload.get('mimeType') == 'multipart/mixed':
                parts = payload.get('parts', [])
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        return self._decode_body(part.get('body', {}))
                return ""
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting message body: {e}")
            return ""
    
    def _extract_attachments(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachment information from a Gmail message."""
        attachments: List[Dict[str, Any]] = []
        
        try:
            payload = message.get('payload', {})
            
            def process_parts(parts: List[Dict[str, Any]]) -> None:
                for part in parts:
                    if part.get('filename'):
                        filename = part['filename']
                        if self._check_attachment_hit(filename):
                            attachments.append({
                                'filename': filename,
                                'mimeType': part.get('mimeType', ''),
                                'size': part.get('body', {}).get('size', 0),
                                'attachmentId': part.get('body', {}).get('attachmentId', '')
                            })
                    
                    # Recursively process nested parts
                    if part.get('parts'):
                        process_parts(part['parts'])
            
            # Process main payload
            if payload.get('parts'):
                process_parts(payload['parts'])
            elif payload.get('filename') and self._check_attachment_hit(payload['filename']):
                attachments.append({
                    'filename': payload['filename'],
                    'mimeType': payload.get('mimeType', ''),
                    'size': payload.get('body', {}).get('size', 0),
                    'attachmentId': payload.get('body', {}).get('attachmentId', '')
                })
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error extracting attachments: {e}")
            return []
    
    def _decode_body(self, body: Dict[str, Any]) -> str:
        """Decode message body content."""
        try:
            data = body.get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
            return ""
        except Exception as e:
            logger.error(f"Error decoding body: {e}")
            return ""
    
    def get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific email."""
        if not self.service:
            self._authenticate()
        
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            return self._process_message(message)
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return None
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return None 