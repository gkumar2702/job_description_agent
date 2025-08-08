"""
Minimal test for EmailCollector without dependencies.
"""

import unittest
from unittest.mock import MagicMock, patch
import base64

class Config:
    """Mock Config class."""
    def __init__(self):
        self.GMAIL_REFRESH_TOKEN = "test_token"

class EmailCollector:
    """Minimal EmailCollector for testing."""
    
    def __init__(self, config):
        self.config = config
        self.service = None
        self.credentials = None
        
        # Constants for email filtering
        self.allowed_domains = [
            'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
            'careerbuilder.com', 'ziprecruiter.com', 'simplyhired.com',
            'dice.com', 'angel.co', 'stackoverflow.com', 'github.com',
            'lever.co', 'greenhouse.io', 'workday.com', 'bamboohr.com',
            'naukri.com', 'mailb.linkedin.com', 'bounce.linkedin.com'
        ]
        
        self.job_keywords = [
            'job description', 'position description', 'role description',
            'we are hiring', 'join our team', 'career opportunity',
            'open position', 'job opening', 'hiring for', 'apply now',
            'job posting', 'career opening', 'employment opportunity',
            'Job |', 'Job Opportunity', 'AI Engineer', 'Data Scientist', 
            'Lead Data Scientist', 'Software Engineer', 'Developer',
            'inmail-hit-reply@linkedin.com', '✉️ Job', 'Job |',
            'LPA', 'salary', 'remote', 'hybrid', 'bangalore', 'bengaluru'
        ]
        
        self.jd_attachment_pattern = r'\.(pdf|doc|docx|txt)$'
    
    def _check_domain_match(self, sender: str) -> bool:
        """Check if sender's domain is in allowed domains."""
        try:
            domain = sender.split('@')[1].lower()
            return any(domain.endswith(allowed) for allowed in self.allowed_domains)
        except IndexError:
            return False
    
    def _check_keyword_hit(self, text: str) -> bool:
        """Check if text contains any job-related keywords."""
        text = text.lower()
        return any(keyword.lower() in text for keyword in self.job_keywords)
    
    def _check_attachment_hit(self, filename: str) -> bool:
        """Check if filename matches JD attachment pattern."""
        import re
        return bool(re.search(self.jd_attachment_pattern, filename, re.IGNORECASE))
    
    def _decode_body(self, body: dict) -> str:
        """Decode email body from base64."""
        try:
            if 'data' in body:
                return base64.urlsafe_b64decode(body['data']).decode('utf-8')
        except Exception:
            pass
        return ''
    
    def _is_likely_job_description(self, subject: str, sender: str) -> bool:
        """Check if email is likely a job description."""
        return (
            self._check_domain_match(sender) or
            self._check_keyword_hit(subject) or
            self._check_keyword_hit(sender)
        )

class TestEmailCollector(unittest.TestCase):
    """Test cases for EmailCollector functionality."""
    
    def setUp(self):
        """Set up test cases."""
        self.config = Config()
        self.collector = EmailCollector(self.config)
        
        # Sample email data
        self.sample_email_1 = {
            "id": "msg_1",
            "threadId": "thread_1",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Job opportunity for Lead Data Scientist",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Rashi Singh <inmail-hit-reply@linkedin.com>"},
                    {"name": "Subject", "value": "Job Opportunity - Lead Data Scientist | ₹ 50 LPA (max) | Bangalore (2‑day Hybrid)"},
                    {"name": "To", "value": "test@example.com"},
                    {"name": "Date", "value": "Fri, 25 Jul 2025 14:23:07 +0000"}
                ],
                "mimeType": "multipart/alternative",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": "SSdtIGhpcmluZyBmb3IgTGVhZCBEYXRhIFNjaWVudGlzdCBhdCBBY3VpdHkgS25vd2xlZGdlIFBhcnRuZXJzLgoKTG9jYXRpb246IEJhbmdhbG9yZSDigKIgaHlicmlkIDIgZGF5cwpFeHBlcmllbmNlOiA3LTkgeWVhcnMKQ1RDOiDigrk1MCBMUEEgKG1heCkKClJlcXVpcmVkIFNraWxsczoKLSBQeXRob24sIFIsIFNRTAotIFRlbnNvckZsb3csIFB5VG9yY2gsIFNjaWtpdC1sZWFybgotIE1hY2hpbmUgTGVhcm5pbmcsIERlZXAgTGVhcm5pbmcKLSBEYXRhIEFuYWx5c2lzLCBTdGF0aXN0aWNhbCBNb2RlbGluZwotIEFXUywgRG9ja2VyLCBLdWJlcm5ldGVz"
                        }
                    },
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": "PGh0bWw+PGJvZHk+SSdtIGhpcmluZyBmb3IgTGVhZCBEYXRhIFNjaWVudGlzdCBhdCBBY3VpdHkgS25vd2xlZGdlIFBhcnRuZXJzLjxicj48YnI+TG9jYXRpb246IEJhbmdhbG9yZSDigKIgaHlicmlkIDIgZGF5czxicj5FeHBlcmllbmNlOiA3LTkgeWVhcnM8YnI+Q1RDOiDigrk1MCBMUEEgKG1heCk8YnI+PGJyPlJlcXVpcmVkIFNraWxsczo8YnI+LSBQeXRob24sIFIsIFNRTDxicj4tIFRlbnNvckZsb3csIFB5VG9yY2gsIFNjaWtpdC1sZWFybjxicj4tIE1hY2hpbmUgTGVhcm5pbmcsIERlZXAgTGVhcm5pbmc8YnI+LSBEYXRhIEFuYWx5c2lzLCBTdGF0aXN0aWNhbCBNb2RlbGluZzxicj4tIEFXUywgRG9ja2VyLCBLdWJlcm5ldGVzPC9ib2R5PjwvaHRtbD4="
                        }
                    }
                ]
            }
        }
        
        self.sample_email_2 = {
            "id": "msg_2",
            "threadId": "thread_2",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Job opportunity for AI Engineer",
            "payload": {
                "headers": [
                    {"name": "From", "value": "UST (www.ust.com) Careers <careers@ust.com>"},
                    {"name": "Subject", "value": "AI Engineer ll Bangalore (Manyata Tech Park)"},
                    {"name": "To", "value": "test@example.com"},
                    {"name": "Date", "value": "Fri, 25 Jul 2025 14:23:07 +0000"}
                ],
                "mimeType": "multipart/alternative",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": "VVNUICAod3d3LnVzdC5jb20pIGlzIGxvb2tpbmcgZm9yIEFJIEVuZ2luZWVycwoKTG9jYXRpb246IEJhbmdhbG9yZSAoTWFueWF0YSBUZWNoIFBhcmspCkV4cGVyaWVuY2U6IDUrIFllYXJzCgpSZXF1aXJlZCBTa2lsbHM6Ci0gUHl0aG9uLCBUZW5zb3JGbG93LCBQeVRvcmNoCi0gTkxQLCBDb21wdXRlciBWaXNpb24KLSBBVVMsIEF6dXJlCi0gQ0kvQ0QsIERvY2tlcg=="
                        }
                    },
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": "PGh0bWw+PGJvZHk+VVNUICAod3d3LnVzdC5jb20pIGlzIGxvb2tpbmcgZm9yIEFJIEVuZ2luZWVyczxicj48YnI+TG9jYXRpb246IEJhbmdhbG9yZSAoTWFueWF0YSBUZWNoIFBhcmspPGJyPkV4cGVyaWVuY2U6IDUrIFllYXJzPGJyPjxicj5SZXF1aXJlZCBTa2lsbHM6PGJyPi0gUHl0aG9uLCBUZW5zb3JGbG93LCBQeVRvcmNoPGJyPi0gTkxQLCBDb21wdXRlciBWaXNpb248YnI+LSBBVVMsIEF6dXJlPGJyPi0gQ0kvQ0QsIERvY2tlcjwvYm9keT48L2h0bWw+"
                        }
                    }
                ]
            }
        }
    
    def test_check_domain_match(self):
        """Test domain matching."""
        # Test allowed domains
        self.assertTrue(self.collector._check_domain_match('test@linkedin.com'))
        self.assertTrue(self.collector._check_domain_match('test@indeed.com'))
        self.assertTrue(self.collector._check_domain_match('test@naukri.com'))
        
        # Test disallowed domains
        self.assertFalse(self.collector._check_domain_match('test@example.com'))
        self.assertFalse(self.collector._check_domain_match('test@gmail.com'))
        self.assertFalse(self.collector._check_domain_match('test@yahoo.com'))
    
    def test_check_keyword_hit(self):
        """Test keyword matching."""
        # Test job-related keywords
        self.assertTrue(self.collector._check_keyword_hit('Job Description: Software Engineer'))
        self.assertTrue(self.collector._check_keyword_hit('We are hiring Data Scientists'))
        self.assertTrue(self.collector._check_keyword_hit('Career opportunity at Google'))
        
        # Test non-job text
        self.assertFalse(self.collector._check_keyword_hit('Meeting invitation'))
        self.assertFalse(self.collector._check_keyword_hit('Newsletter subscription'))
        self.assertFalse(self.collector._check_keyword_hit('Password reset request'))
    
    def test_check_attachment_hit(self):
        """Test attachment matching."""
        # Test allowed attachment types
        self.assertTrue(self.collector._check_attachment_hit('job_description.pdf'))
        self.assertTrue(self.collector._check_attachment_hit('position_details.doc'))
        self.assertTrue(self.collector._check_attachment_hit('requirements.docx'))
        self.assertTrue(self.collector._check_attachment_hit('jd.txt'))
        
        # Test disallowed attachment types
        self.assertFalse(self.collector._check_attachment_hit('image.jpg'))
        self.assertFalse(self.collector._check_attachment_hit('presentation.ppt'))
        self.assertFalse(self.collector._check_attachment_hit('spreadsheet.xlsx'))
    
    def test_decode_body(self):
        """Test email body decoding."""
        # Test plain text decoding
        body_data = {
            'data': 'SGVsbG8gV29ybGQ='  # Base64 encoded "Hello World"
        }
        decoded_text = self.collector._decode_body(body_data)
        self.assertEqual(decoded_text, 'Hello World')
        
        # Test empty body
        self.assertEqual(self.collector._decode_body({}), '')
        self.assertEqual(self.collector._decode_body({'data': ''}), '')
        
        # Test invalid base64
        self.assertEqual(self.collector._decode_body({'data': 'invalid_base64'}), '')
    
    def test_is_likely_job_description(self):
        """Test job description detection."""
        # Test job-related subjects and senders
        self.assertTrue(self.collector._is_likely_job_description(
            'Job Opportunity: Senior Software Engineer',
            'careers@company.com'
        ))
        self.assertTrue(self.collector._is_likely_job_description(
            'We are hiring Data Scientists',
            'jobs@linkedin.com'
        ))
        self.assertTrue(self.collector._is_likely_job_description(
            'Career opportunity at Google',
            'talent@google.com'
        ))
        
        # Test non-job emails
        self.assertFalse(self.collector._is_likely_job_description(
            'Meeting invitation',
            'calendar@company.com'
        ))
        self.assertFalse(self.collector._is_likely_job_description(
            'Your order confirmation',
            'orders@amazon.com'
        ))
        self.assertFalse(self.collector._is_likely_job_description(
            'Password reset request',
            'support@company.com'
        ))

if __name__ == '__main__':
    unittest.main()