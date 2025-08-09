"""
Tests for EmailSelector component.
"""

import pytest
from unittest.mock import Mock, patch

from ..components.email_selector import EmailSelector
from ..components.jd_parser import JDParser, JobDescription


class TestEmailSelector:
    @pytest.fixture
    def selector(self) -> EmailSelector:
        mock_collector = Mock()
        mock_parser = Mock(spec=JDParser)
        return EmailSelector(mock_collector, mock_parser)

    def test_extract_email_preview_plain_text(self, selector: EmailSelector) -> None:
        email = {
            'body': 'Hello,\nWe have a Software Engineer opening in Bengaluru.\nThanks',
        }
        preview = selector._extract_email_preview(email)
        assert 'Software Engineer opening' in preview
        assert len(preview) <= 200

    def test_extract_email_preview_from_message_payload(self, selector: EmailSelector) -> None:
        email = {
            'message': {
                'payload': {
                    'mimeType': 'text/plain',
                    'body': {'data': 'Role: Data Scientist\nLocation: Bangalore'}
                }
            }
        }
        preview = selector._extract_email_preview(email)
        assert 'Data Scientist' in preview

    @pytest.mark.asyncio
    async def test_process_selected_emails(self, selector: EmailSelector) -> None:
        # Prepare a realistic selected email
        email = {
            'from': 'recruiter@example.com',
            'subject': 'Hiring: Software Engineer',
            'date': '2025-01-01',
            'body': 'We are hiring a Software Engineer with Python and AWS experience.'
        }

        # Mock collector and parser behavior
        selector.email_collector.extract_job_description_from_email.return_value = (
            'Company: ExampleCorp\nRole: Software Engineer\nLocation: Bengaluru\nExperience: 3-5 years\nSkills: Python, AWS'
        )
        selector.jd_parser.parse_job_description.return_value = JobDescription(
            company='ExampleCorp',
            role='Software Engineer',
            location='Bengaluru',
            experience_years=4,
            skills=['Python', 'AWS'],
            content='JD content',
            email_id='email_1',
            confidence_score=0.8,
            salary_lpa=0.0,
            requirements=[],
            responsibilities=[],
            parsing_metadata={}
        )

        results = await selector.process_selected_emails([email])
        assert len(results) == 1
        jd = results[0]['job_description']
        assert jd.company == 'ExampleCorp'
        assert jd.role == 'Software Engineer'
        assert jd.experience_years == 4


