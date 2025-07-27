"""
Email collector component for fetching job description emails from Gmail.
"""

import base64
import email
import os
import json
import webbrowser
import re
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
    
    # Allowed domains for job-related emails
    ALLOWED_DOMAINS = [
        "linkedin.com", "naukri.com", "indeed.com", "monster.com",
        "glassdoor.com", "careerbuilder.com", "simplyhired.com",
        "ziprecruiter.com", "dice.com", "angel.co", "stackoverflow.com"
    ]
    
    # Keywords that indicate job descriptions
    JOB_KEYWORDS = [
        "job", "job opportunity", "hiring", "vacancy", "opening", "career",
        "position", "role", "employment", "recruitment", "staffing",
        "job description", "job posting", "career opportunity", "we are hiring",
        "open position", "job opening", "employment opportunity",
        "join our team", "apply now", "job requirements",
        "qualifications", "responsibilities", "job duties"
    ]
    
    # Regex pattern for job description attachments
    JD_ATTACHMENT_PATTERN = re.compile(r'.*(JD|job[-_ ]?description).*(pdf|docx?)$', re.IGNORECASE)
    
    def __init__(self):
        """Initialize the email collector."""
        self.service = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Gmail API."""
        creds = None
        token_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'token.json')
        
        # Check if we have valid credentials from token file
        if os.path.exists(token_path):
            try:
                with open(token_path, 'r') as token:
                    creds = Credentials.from_authorized_user_info(json.load(token), self.SCOPES)
                logger.info("Loaded credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load token file: {e}")
        
        # Check if we have valid credentials from environment variables
        if not creds and Config.GMAIL_REFRESH_TOKEN:
            try:
                creds = Credentials(
                    token=None,
                    refresh_token=Config.GMAIL_REFRESH_TOKEN,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=Config.GMAIL_CLIENT_ID,
                    client_secret=Config.GMAIL_CLIENT_SECRET,
                    scopes=self.SCOPES
                )
                logger.info("Loaded credentials from environment variables")
            except Exception as e:
                logger.warning(f"Failed to load credentials from environment: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                logger.error("No valid Gmail credentials found.")
                self._print_oauth_instructions()
                return
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Successfully authenticated with Gmail API")
            
            # Save credentials to token file for future use
            if not os.path.exists(token_path):
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Saved credentials to token file")
                
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            self.service = None
    
    def _print_oauth_instructions(self) -> None:
        """Print instructions for setting up OAuth credentials."""
        print("\n" + "="*60)
        print("🔐 GMAIL API SETUP INSTRUCTIONS")
        print("="*60)
        print("To use Gmail integration, you need to set up OAuth2 credentials:")
        print()
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Gmail API' and enable it")
        print("4. Create OAuth2 credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
        print("   - Choose 'Desktop application'")
        print("   - Download the JSON file")
        print("5. Extract credentials from the JSON file:")
        print("   - client_id: from 'client_id' field")
        print("   - client_secret: from 'client_secret' field")
        print()
        print("6. Set up your .env file:")
        print("   GMAIL_CLIENT_ID=your_client_id_here")
        print("   GMAIL_CLIENT_SECRET=your_client_secret_here")
        print()
        print("7. Run the authentication flow:")
        print("   python -c \"from jd_agent.components.email_collector import EmailCollector; EmailCollector()\"")
        print()
        print("This will open a browser window for authentication.")
        print("After authentication, the refresh token will be saved automatically.")
        print("="*60)
        print()
    
    def _get_oauth_credentials(self) -> Optional[Credentials]:
        """Get OAuth credentials through interactive flow."""
        try:
            # Check if credentials file exists
            creds_path = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json')
            
            if not os.path.exists(creds_path):
                print(f"\n❌ Credentials file not found at: {creds_path}")
                print("Please download the OAuth2 credentials JSON file from Google Cloud Console")
                print("and save it as 'credentials.json' in the project root directory.")
                return None
            
            # Load credentials from file
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            
            # Create flow
            flow = InstalledAppFlow.from_client_config(
                creds_data, 
                self.SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            # Run the flow
            print("\n🔐 Opening browser for Gmail authentication...")
            print("Please complete the authentication in your browser.")
            print("If the browser doesn't open automatically, copy and paste the URL.")
            
            creds = flow.run_local_server(port=0)
            return creds
            
        except Exception as e:
            logger.error(f"Failed to get OAuth credentials: {e}")
            return None
    
    def _build_enhanced_search_query(self, days_back: int = 30) -> str:
        """
        Build an enhanced search query that captures all potential job description emails.
        
        Args:
            days_back: Number of days back to search for emails
            
        Returns:
            str: Gmail search query
        """
        # Base query components
        base_filters = "in:anywhere NOT in:spam"
        
        # Date filter
        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        date_filter = f"after:{after_date}"
        
        # Domain filter
        domain_queries = [f"from:{domain}" for domain in self.ALLOWED_DOMAINS]
        domain_filter = f"({' OR '.join(domain_queries)})"
        
        # Keyword filter
        keyword_queries = [f'"{keyword}"' for keyword in self.JOB_KEYWORDS]
        keyword_filter = f"({' OR '.join(keyword_queries)})"
        
        # Attachment filter
        attachment_filter = "has:attachment"
        
        # Combine all filters
        # Return emails that match: (domain OR keyword) AND (attachment OR keyword in subject/body)
        query = f"{base_filters} {date_filter} AND ({domain_filter} OR {keyword_filter})"
        
        logger.info(f"Built enhanced search query: {query}")
        return query
    
    def fetch_job_description_threads(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Returns threads likely to contain a job description.

        Detection logic:
        - domain_match: sender domain in ALLOWED_DOMAINS
        - keyword_hit: any KEYWORD in subject or snippet
        - attachment_hit: attachment filename regex
        A thread is returned if (domain_match OR keyword_hit OR attachment_hit) is True.
        
        Args:
            days_back: Number of days back to search for emails
            
        Returns:
            List[Dict[str, Any]]: List of thread data with detection details
        """
        if not self.service:
            logger.error("Gmail service not available")
            return []
        
        try:
            # Build enhanced search query
            query = self._build_enhanced_search_query(days_back)
            
            # Search for threads
            results = self.service.users().threads().list(
                userId='me', 
                q=query,
                maxResults=100
            ).execute()
            
            threads = results.get('threads', [])
            if not threads:
                logger.info("No job description threads found")
                return []
            
            logger.info(f"Found {len(threads)} potential job description threads")
            
            # Process each thread
            job_threads = []
            for thread in threads:
                try:
                    thread_data = self._analyze_thread_for_job_description(thread['id'])
                    if thread_data:
                        job_threads.append(thread_data)
                except Exception as e:
                    logger.error(f"Failed to analyze thread {thread['id']}: {e}")
                    continue
            
            logger.info(f"Successfully identified {len(job_threads)} job description threads")
            return job_threads
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching threads: {e}")
            return []
    
    def _analyze_thread_for_job_description(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a thread to determine if it contains job descriptions.
        
        Args:
            thread_id: Gmail thread ID
            
        Returns:
            Optional[Dict[str, Any]]: Thread analysis data or None
        """
        try:
            # Get thread details
            thread = self.service.users().threads().get(
                userId='me', 
                id=thread_id
            ).execute()
            
            messages = thread.get('messages', [])
            if not messages:
                return None
            
            # Analyze each message in the thread
            thread_analysis = {
                'thread_id': thread_id,
                'message_count': len(messages),
                'detection_reasons': [],
                'messages': [],
                'has_job_description': False
            }
            
            for message in messages:
                message_analysis = self._analyze_message_for_job_description(message)
                if message_analysis:
                    thread_analysis['messages'].append(message_analysis)
                    thread_analysis['detection_reasons'].extend(message_analysis['detection_reasons'])
                    if message_analysis['is_job_description']:
                        thread_analysis['has_job_description'] = True
            
            # Remove duplicate detection reasons
            thread_analysis['detection_reasons'] = list(set(thread_analysis['detection_reasons']))
            
            # Return thread if it contains job descriptions
            if thread_analysis['has_job_description']:
                return thread_analysis
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to analyze thread {thread_id}: {e}")
            return None
    
    def _analyze_message_for_job_description(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a message to determine if it contains job descriptions.
        
        Args:
            message: Gmail message data
            
        Returns:
            Optional[Dict[str, Any]]: Message analysis data or None
        """
        try:
            headers = message['payload']['headers']
            
            # Extract basic information
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract email body
            body = self._extract_email_body(message['payload'])
            snippet = message.get('snippet', '')
            
            # Analyze detection criteria
            detection_reasons = []
            is_job_description = False
            
            # 1. Domain match
            domain_match = self._check_domain_match(sender)
            if domain_match:
                detection_reasons.append(f"domain_match:{domain_match}")
                is_job_description = True
            
            # 2. Keyword hit
            keyword_hit = self._check_keyword_hit(subject, body, snippet)
            if keyword_hit:
                detection_reasons.append(f"keyword_hit:{keyword_hit}")
                is_job_description = True
            
            # 3. Attachment hit
            attachment_hit = self._check_attachment_hit(message['payload'])
            if attachment_hit:
                detection_reasons.append(f"attachment_hit:{attachment_hit}")
                is_job_description = True
            
            if is_job_description:
                return {
                    'message_id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body': body,
                    'snippet': snippet,
                    'detection_reasons': detection_reasons,
                    'is_job_description': True,
                    'domain_match': domain_match,
                    'keyword_hit': keyword_hit,
                    'attachment_hit': attachment_hit
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to analyze message {message.get('id', 'unknown')}: {e}")
            return None
    
    def _check_domain_match(self, sender: str) -> Optional[str]:
        """
        Check if sender domain is in allowed domains.
        
        Args:
            sender: Email sender address
            
        Returns:
            Optional[str]: Matched domain or None
        """
        try:
            # Extract domain from email address
            if '@' in sender:
                domain = sender.split('@')[1].lower()
                for allowed_domain in self.ALLOWED_DOMAINS:
                    if domain == allowed_domain or domain.endswith(f'.{allowed_domain}'):
                        return allowed_domain
        except Exception as e:
            logger.debug(f"Error checking domain match: {e}")
        
        return None
    
    def _check_keyword_hit(self, subject: str, body: str, snippet: str) -> Optional[str]:
        """
        Check if any job keywords are present in subject, body, or snippet.
        
        Args:
            subject: Email subject
            body: Email body
            snippet: Email snippet
            
        Returns:
            Optional[str]: Matched keyword or None
        """
        text = f"{subject} {body} {snippet}".lower()
        
        # Sort keywords by length (longest first) to avoid partial matches
        sorted_keywords = sorted(self.JOB_KEYWORDS, key=len, reverse=True)
        
        for keyword in sorted_keywords:
            keyword_lower = keyword.lower()
            # Use word boundaries to avoid partial matches
            import re
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            if re.search(pattern, text):
                return keyword
        
        return None
    
    def _check_attachment_hit(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Check if any attachments match the job description pattern.
        
        Args:
            payload: Message payload
            
        Returns:
            Optional[str]: Matched attachment filename or None
        """
        try:
            attachments = []
            self._extract_attachments(payload, attachments)
            
            for attachment in attachments:
                filename = attachment.get('filename', '')
                if self.JD_ATTACHMENT_PATTERN.match(filename):
                    return filename
            
        except Exception as e:
            logger.debug(f"Error checking attachment hit: {e}")
        
        return None
    
    def fetch_jd_emails(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch job description emails from Gmail (legacy method for backward compatibility).
        
        Args:
            days_back: Number of days back to search for emails
            
        Returns:
            List[Dict[str, Any]]: List of email data
        """
        # Use the new enhanced method and convert to legacy format
        threads = self.fetch_job_description_threads(days_back)
        
        emails = []
        for thread in threads:
            for message in thread.get('messages', []):
                emails.append({
                    'id': message['message_id'],
                    'subject': message['subject'],
                    'from': message['sender'],
                    'date': message['date'],
                    'body': message['body'],
                    'thread_id': thread['thread_id'],
                    'snippet': message['snippet']
                })
        
        return emails
    
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
        Determine if an email contains a job description (legacy method).
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            bool: True if email appears to be a job description
        """
        # Use the new keyword detection logic
        text = f"{subject} {body}".lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in self.JOB_KEYWORDS if keyword.lower() in text)
        
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