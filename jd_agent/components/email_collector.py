"""
Email collector component for fetching job description emails from Gmail.
"""

import base64
import email
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmailCollector:
    """Collects job description emails from Gmail."""
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        """Initialize the email collector."""
        self.service = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Gmail API."""
        creds = None
        
        # Check if we have valid credentials
        if Config.GMAIL_REFRESH_TOKEN:
            creds = Credentials(
                token=None,
                refresh_token=Config.GMAIL_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=Config.GMAIL_CLIENT_ID,
                client_secret=Config.GMAIL_CLIENT_SECRET,
                scopes=self.SCOPES
            )
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                logger.error("No valid Gmail credentials found. Please set up OAuth2 credentials.")
                return
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Successfully authenticated with Gmail API")
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            self.service = None
    
    def fetch_jd_emails(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch job description emails from Gmail.
        
        Args:
            days_back: Number of days back to search for emails
            
        Returns:
            List[Dict[str, Any]]: List of email data
        """
        if not self.service:
            logger.error("Gmail service not available")
            return []
        
        try:
            # Calculate date range
            after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Build search query
            query = f"{Config.EMAIL_SEARCH_QUERY} after:{after_date}"
            logger.info(f"Searching for emails with query: {query}")
            
            # Search for emails
            results = self.service.users().messages().list(
                userId='me', 
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                logger.info("No job description emails found")
                return []
            
            logger.info(f"Found {len(messages)} potential job description emails")
            
            # Fetch full email details
            emails = []
            for message in messages:
                try:
                    email_data = self._fetch_email_details(message['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Failed to fetch email {message['id']}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(emails)} emails")
            return emails
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching emails: {e}")
            return []
    
    def _fetch_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific email.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Optional[Dict[str, Any]]: Email details or None
        """
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract basic email information
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract email body
            body = self._extract_email_body(message['payload'])
            
            # Check if this looks like a job description
            if self._is_job_description(subject, body):
                return {
                    'id': message_id,
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body': body,
                    'thread_id': message.get('threadId', ''),
                    'snippet': message.get('snippet', '')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch email details for {message_id}: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from Gmail message payload.
        
        Args:
            payload: Gmail message payload
            
        Returns:
            str: Email body text
        """
        body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body += base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    # Fallback to HTML if plain text not available
                    if not body and 'data' in part['body']:
                        body += base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
        else:
            # Simple message
            if 'data' in payload['body']:
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
        
        return body
    
    def _is_job_description(self, subject: str, body: str) -> bool:
        """
        Determine if an email contains a job description.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            bool: True if email appears to be a job description
        """
        # Keywords that indicate a job description
        jd_keywords = [
            'job description', 'job posting', 'position description',
            'role description', 'career opportunity', 'we are hiring',
            'open position', 'job opening', 'employment opportunity',
            'join our team', 'apply now', 'job requirements',
            'qualifications', 'responsibilities', 'job duties'
        ]
        
        # Check subject and body for keywords
        text = f"{subject} {body}".lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in jd_keywords if keyword in text)
        
        # Consider it a job description if we have at least 2 keyword matches
        return matches >= 2
    
    def get_email_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """
        Get attachments from an email.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            List[Dict[str, Any]]: List of attachment information
        """
        if not self.service:
            return []
        
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            attachments = []
            self._extract_attachments(message['payload'], attachments)
            
            return attachments
            
        except Exception as e:
            logger.error(f"Failed to get attachments for {message_id}: {e}")
            return []
    
    def _extract_attachments(self, payload: Dict[str, Any], 
                           attachments: List[Dict[str, Any]]) -> None:
        """
        Recursively extract attachments from message payload.
        
        Args:
            payload: Message payload
            attachments: List to store attachment information
        """
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    attachments.append({
                        'id': part['body'].get('attachmentId'),
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part['body'].get('size', 0)
                    })
                else:
                    self._extract_attachments(part, attachments) 