"""
Unit tests for EmailCollector component.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ..components.email_collector import EmailCollector


class TestEmailCollector:
    """Test cases for EmailCollector."""
    
    @pytest.fixture
    def collector(self):
        """Create an EmailCollector instance for testing."""
        with patch('googleapiclient.discovery.build'):
            return EmailCollector()
    
    def test_is_job_description_valid(self, collector):
        """Test job description detection with valid content."""
        subject = "Software Engineer Position at Google"
        body = """
        We are looking for a Software Engineer to join our team.
        Job Description:
        - 5+ years of experience
        - Python and Java skills
        - Join our team and apply now
        """
        
        assert collector._is_job_description(subject, body) is True
    
    def test_is_job_description_invalid(self, collector):
        """Test job description detection with invalid content."""
        subject = "Weekly Newsletter"
        body = "This is just a regular newsletter with no job information."
        
        assert collector._is_job_description(subject, body) is False
    
    def test_is_job_description_edge_cases(self, collector):
        """Test job description detection with edge cases."""
        # Test with minimal keywords
        subject = "Job posting"
        body = "We are hiring"
        assert collector._is_job_description(subject, body) is True
        
        # Test with case insensitive matching
        subject = "JOB DESCRIPTION"
        body = "We are looking for candidates"
        assert collector._is_job_description(subject, body) is True
        
        # Test with insufficient keywords
        subject = "Random email"
        body = "This email contains the word job but not enough context"
        assert collector._is_job_description(subject, body) is False
    
    def test_extract_email_body_simple(self, collector):
        """Test extracting email body from simple message."""
        payload = {
            'body': {
                'data': 'VGVzdCBjb250ZW50'  # Base64 encoded "Test content"
            }
        }
        
        body = collector._extract_email_body(payload)
        assert body == "Test content"
    
    def test_extract_email_body_multipart(self, collector):
        """Test extracting email body from multipart message."""
        payload = {
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'data': 'VGV4dCBjb250ZW50'  # Base64 encoded "Text content"
                    }
                },
                {
                    'mimeType': 'text/html',
                    'body': {
                        'data': 'SFRNTCBjb250ZW50'  # Base64 encoded "HTML content"
                    }
                }
            ]
        }
        
        body = collector._extract_email_body(payload)
        assert body == "Text content"  # Should prefer plain text
    
    def test_extract_email_body_html_fallback(self, collector):
        """Test extracting email body with HTML fallback."""
        payload = {
            'parts': [
                {
                    'mimeType': 'text/html',
                    'body': {
                        'data': 'SFRNTCBjb250ZW50'  # Base64 encoded "HTML content"
                    }
                }
            ]
        }
        
        body = collector._extract_email_body(payload)
        assert body == "HTML content"  # Should use HTML if no plain text
    
    def test_extract_email_body_no_data(self, collector):
        """Test extracting email body when no data is available."""
        payload = {
            'body': {}
        }
        
        body = collector._extract_email_body(payload)
        assert body == ""
    
    def test_extract_email_body_invalid_base64(self, collector):
        """Test extracting email body with invalid base64 data."""
        payload = {
            'body': {
                'data': 'invalid-base64-data'
            }
        }
        
        # Should handle the error gracefully
        body = collector._extract_email_body(payload)
        assert body == ""
    
    @patch('googleapiclient.discovery.build')
    def test_authenticate_success(self, mock_build):
        """Test successful authentication."""
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        collector = EmailCollector()
        
        assert collector.service is not None
        mock_build.assert_called_once()
    
    @patch('googleapiclient.discovery.build')
    def test_authenticate_failure(self, mock_build):
        """Test authentication failure."""
        mock_build.side_effect = Exception("Authentication failed")
        
        collector = EmailCollector()
        
        assert collector.service is None
    
    @patch('googleapiclient.discovery.build')
    def test_fetch_email_details_success(self, mock_build):
        """Test successful email details fetching."""
        # Mock Gmail service
        mock_service = Mock()
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            'id': 'test_message_id',
            'threadId': 'test_thread_id',
            'snippet': 'Test snippet',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Date', 'value': '2023-01-01'},
                ],
                'body': {
                    'data': 'VGVzdCBib2R5'  # Base64 encoded "Test body"
                }
            }
        }
        mock_build.return_value = mock_service
        
        collector = EmailCollector()
        collector.service = mock_service
        
        # Mock job description detection
        with patch.object(collector, '_is_job_description', return_value=True):
            email_data = collector._fetch_email_details('test_message_id')
            
            assert email_data is not None
            assert email_data['id'] == 'test_message_id'
            assert email_data['subject'] == 'Test Subject'
            assert email_data['sender'] == 'test@example.com'
            assert email_data['body'] == 'Test body'
    
    @patch('googleapiclient.discovery.build')
    def test_fetch_email_details_not_jd(self, mock_build):
        """Test fetching email details that is not a job description."""
        # Mock Gmail service
        mock_service = Mock()
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            'id': 'test_message_id',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Regular Email'},
                ],
                'body': {
                    'data': 'UmVndWxhciBlbWFpbA=='  # Base64 encoded "Regular email"
                }
            }
        }
        mock_build.return_value = mock_service
        
        collector = EmailCollector()
        collector.service = mock_service
        
        # Mock job description detection to return False
        with patch.object(collector, '_is_job_description', return_value=False):
            email_data = collector._fetch_email_details('test_message_id')
            
            assert email_data is None
    
    @patch('googleapiclient.discovery.build')
    def test_fetch_email_details_error(self, mock_build):
        """Test email details fetching with error."""
        # Mock Gmail service that raises an exception
        mock_service = Mock()
        mock_service.users.return_value.messages.return_value.get.return_value.execute.side_effect = Exception("API error")
        mock_build.return_value = mock_service
        
        collector = EmailCollector()
        collector.service = mock_service
        
        email_data = collector._fetch_email_details('test_message_id')
        
        assert email_data is None
    
    @patch('googleapiclient.discovery.build')
    def test_fetch_jd_emails_success(self, mock_build):
        """Test successful JD email fetching."""
        # Mock Gmail service
        mock_service = Mock()
        
        # Mock list messages response
        mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'},
            ]
        }
        
        # Mock get message responses
        def mock_get_message(message_id):
            mock_message = Mock()
            mock_message.execute.return_value = {
                'id': message_id,
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': f'Job Description {message_id}'},
                    ],
                    'body': {
                        'data': 'VGVzdCBib2R5'  # Base64 encoded "Test body"
                    }
                }
            }
            return mock_message
        
        mock_service.users.return_value.messages.return_value.get.side_effect = mock_get_message
        mock_build.return_value = mock_service
        
        collector = EmailCollector()
        collector.service = mock_service
        
        # Mock job description detection
        with patch.object(collector, '_is_job_description', return_value=True):
            emails = collector.fetch_jd_emails()
            
            assert len(emails) == 2
            assert emails[0]['id'] == 'msg1'
            assert emails[1]['id'] == 'msg2'
    
    @patch('googleapiclient.discovery.build')
    def test_fetch_jd_emails_no_messages(self, mock_build):
        """Test JD email fetching when no messages are found."""
        # Mock Gmail service
        mock_service = Mock()
        mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            'messages': []
        }
        mock_build.return_value = mock_service
        
        collector = EmailCollector()
        collector.service = mock_service
        
        emails = collector.fetch_jd_emails()
        
        assert emails == []
    
    @patch('googleapiclient.discovery.build')
    def test_fetch_jd_emails_service_unavailable(self, mock_build):
        """Test JD email fetching when service is unavailable."""
        mock_build.return_value = None
        
        collector = EmailCollector()
        collector.service = None
        
        emails = collector.fetch_jd_emails()
        
        assert emails == []
    
    def test_extract_attachments(self, collector):
        """Test attachment extraction."""
        payload = {
            'parts': [
                {
                    'filename': 'document.pdf',
                    'body': {
                        'attachmentId': 'att123',
                        'size': 1024
                    }
                },
                {
                    'parts': [
                        {
                            'filename': 'image.jpg',
                            'body': {
                                'attachmentId': 'att456',
                                'size': 2048
                            }
                        }
                    ]
                }
            ]
        }
        
        attachments = []
        collector._extract_attachments(payload, attachments)
        
        assert len(attachments) == 2
        assert attachments[0]['filename'] == 'document.pdf'
        assert attachments[1]['filename'] == 'image.jpg'
    
    def test_extract_attachments_no_attachments(self, collector):
        """Test attachment extraction when no attachments exist."""
        payload = {
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'data': 'VGVzdCBjb250ZW50'
                    }
                }
            ]
        }
        
        attachments = []
        collector._extract_attachments(payload, attachments)
        
        assert len(attachments) == 0 