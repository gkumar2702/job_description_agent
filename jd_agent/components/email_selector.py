"""
Email Selector component for interactive email selection and preprocessing.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger
from .email_collector import EmailCollector
from .jd_parser import JDParser

logger = get_logger(__name__)


class EmailSelector:
    """Interactive email selection and preprocessing component."""
    
    def __init__(self, email_collector: EmailCollector, jd_parser: JDParser):
        """Initialize the email selector."""
        self.email_collector = email_collector
        self.jd_parser = jd_parser
    
    async def fetch_and_display_emails(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch emails and display them for user selection.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List[Dict[str, Any]]: Selected emails for processing
        """
        print("🔍 Fetching job description emails...")
        
        # Fetch emails
        emails = self.email_collector.fetch_job_description_emails(max_results)
        
        if not emails:
            print("❌ No job description emails found!")
            return []
        
        print(f"\n📧 Found {len(emails)} potential job description emails:")
        print("=" * 80)
        
        # Display emails with selection options
        selected_emails = []
        
        for i, email in enumerate(emails, 1):
            subject = email.get('subject', 'No Subject')
            sender = email.get('from', 'Unknown Sender')
            date = email.get('date', 'Unknown Date')
            
            # Extract basic info for preview
            preview = self._extract_email_preview(email)
            
            print(f"\n📧 Email {i}:")
            print(f"   Subject: {subject}")
            print(f"   From: {sender}")
            print(f"   Date: {date}")
            print(f"   Preview: {preview[:100]}...")
            
            # Ask user if they want to process this email
            while True:
                choice = input(f"\nProcess Email {i}? (y/n/s for skip all): ").lower().strip()
                if choice in ['y', 'n', 's']:
                    break
                print("Please enter 'y', 'n', or 's'")
            
            if choice == 'y':
                selected_emails.append(email)
                print(f"✅ Email {i} selected for processing")
            elif choice == 's':
                print("⏭️  Skipping remaining emails...")
                break
            else:
                print(f"⏭️  Email {i} skipped")
        
        print(f"\n📊 Summary: {len(selected_emails)} emails selected for processing")
        return selected_emails
    
    def _extract_email_preview(self, email: Dict[str, Any]) -> str:
        """
        Extract a preview of the email content.
        
        Args:
            email: Email data
            
        Returns:
            str: Email preview
        """
        # Try to get body content
        body = email.get('body', '')
        if not body:
            # Try to extract from message data
            message = email.get('message', {})
            if message:
                body = self._extract_message_body(message)
        
        # Clean and return preview
        if body:
            # Remove HTML tags and extra whitespace
            import re
            clean_body = re.sub(r'<[^>]+>', '', body)
            clean_body = re.sub(r'\s+', ' ', clean_body).strip()
            return clean_body[:200]  # Limit to 200 characters
        
        return "No content available"
    
    def _extract_message_body(self, message: Dict[str, Any]) -> str:
        """
        Extract body content from Gmail message data.
        
        Args:
            message: Gmail message data
            
        Returns:
            str: Message body
        """
        try:
            # Try to get payload
            payload = message.get('payload', {})
            if not payload:
                return ""
            
            # Check for multipart message
            if payload.get('mimeType') == 'multipart/alternative':
                parts = payload.get('parts', [])
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        return part.get('body', {}).get('data', '')
            elif payload.get('mimeType') == 'text/plain':
                return payload.get('body', {}).get('data', '')
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting message body: {e}")
            return ""
    
    async def process_selected_emails(self, selected_emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process selected emails and extract job descriptions.
        
        Args:
            selected_emails: List of selected emails
            
        Returns:
            List[Dict[str, Any]]: Processed job descriptions with metadata
        """
        processed_jds = []
        
        print(f"\n🔄 Processing {len(selected_emails)} selected emails...")
        
        for i, email in enumerate(selected_emails, 1):
            print(f"\n--- Processing Email {i}/{len(selected_emails)} ---")
            
            try:
                # Extract job description from email
                jd_text = self.email_collector.extract_job_description_from_email(email)
                
                if not jd_text:
                    print(f"❌ Could not extract job description from Email {i}")
                    continue
                
                # Parse job description
                jd = self.jd_parser.parse_job_description(jd_text, email.get('from', 'Unknown'))
                
                if not jd:
                    print(f"❌ Could not parse job description from Email {i}")
                    continue
                
                # Create processed result
                processed_jd = {
                    'email_data': email,
                    'job_description': jd,
                    'extracted_text': jd_text,
                    'processed_at': datetime.now().isoformat()
                }
                
                processed_jds.append(processed_jd)
                
                print(f"✅ Successfully processed Email {i}")
                print(f"   Company: {jd.company}")
                print(f"   Role: {jd.role}")
                print(f"   Location: {jd.location}")
                print(f"   Experience: {jd.experience_years} years")
                print(f"   Skills: {len(jd.skills)} skills")
                
            except Exception as e:
                print(f"❌ Error processing Email {i}: {e}")
                continue
        
        print(f"\n📊 Summary: {len(processed_jds)} job descriptions successfully processed")
        return processed_jds 