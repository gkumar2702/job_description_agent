"""
Integration tests for the JD Agent pipeline.

Tests the interaction between different components:
1. Email Collection → JD Parsing
2. JD Parsing → Knowledge Mining
3. Knowledge Mining → Question Generation
4. Question Generation → PDF Export
"""

import os
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from jd_agent.utils.config import Config
from jd_agent.main import JDAgent
from jd_agent.components.jd_parser import JobDescription

# Sample test data
SAMPLE_JD_TEXT = """
Software Engineer
Company: TechCorp
Location: San Francisco, CA

Requirements:
- 5+ years of experience in Python development
- Strong knowledge of web frameworks (Django, Flask)
- Experience with cloud platforms (AWS, GCP)
- Excellent problem-solving skills
- Bachelor's degree in Computer Science or related field

Responsibilities:
- Design and implement scalable backend services
- Collaborate with cross-functional teams
- Write clean, maintainable code
- Participate in code reviews
- Mentor junior developers
"""

SAMPLE_EMAIL_DATA = {
    'subject': 'Software Engineer Position at TechCorp',
    'from': 'recruiter@techcorp.com',
    'date': datetime.now().isoformat(),
    'body': SAMPLE_JD_TEXT
}

@pytest.fixture
def config(tmp_path):
    """Create a test configuration."""
    config = Config()
    # Set test configuration values
    config.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'test-key')
    config.SERPAPI_KEY = os.getenv('SERPAPI_KEY', 'test-key')
    
    # Mock OpenAI client for testing
    config.OPENAI_MODEL = "gpt-3.5-turbo"  # Use a smaller model for testing
    config.MAX_TOKENS = 500  # Limit token usage in tests
    config.TEMPERATURE = 0.0  # Make responses deterministic for testing
    
    # Use in-memory SQLite database for tests
    config.DATABASE_PATH = ":memory:"
    
    # Create a temporary directory for exports
    export_dir = tmp_path / "exports"
    export_dir.mkdir(exist_ok=True)
    config.EXPORT_DIR = str(export_dir)
    
    return config

@pytest.fixture
def jd_agent(config):
    """Create a JDAgent instance with test configuration."""
    return JDAgent(config)

@pytest.mark.asyncio
async def test_process_single_jd_integration(jd_agent):
    """Test the integration of components when processing a single job description."""
    
    # Process the job description
    questions = await jd_agent.process_single_jd(SAMPLE_JD_TEXT, "TechCorp")
    
    # Verify results
    assert questions is not None
    assert isinstance(questions, list)
    assert len(questions) > 0
    
    # Verify question structure
    for question in questions:
        assert 'question' in question
        assert 'difficulty' in question
        assert 'category' in question
        # Note: relevance_score is optional in the current implementation

@pytest.mark.asyncio
async def test_email_to_questions_integration(jd_agent):
    """Test the integration from email processing to question generation."""
    
    # Mock email collection
    with patch.object(jd_agent.email_collector, 'fetch_job_description_emails') as mock_fetch:
        mock_fetch.return_value = [SAMPLE_EMAIL_DATA]
        
        # Process emails
        questions = await jd_agent.process_emails(max_emails=1)
        
        # Verify results
        assert questions is not None
        assert isinstance(questions, list)
        assert len(questions) > 0
        
        # Verify email processing
        mock_fetch.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_full_pipeline_integration(jd_agent):
    """Test the complete pipeline integration."""
    
    # Mock email collection
    with patch.object(jd_agent.email_collector, 'fetch_job_description_emails') as mock_fetch:
        mock_fetch.return_value = [SAMPLE_EMAIL_DATA]
        
        # Run full pipeline
        results = await jd_agent.run_full_pipeline(max_emails=1)
        
        # Verify results structure
        assert 'total_questions' in results
        assert 'duration_seconds' in results
        assert 'questions_by_difficulty' in results
        assert 'average_relevance_score' in results
        assert 'usage_stats' in results
        assert 'export_files' in results
        
        # Verify results content
        assert results['total_questions'] > 0
        assert results['duration_seconds'] > 0
        assert isinstance(results['questions_by_difficulty'], dict)
        assert isinstance(results['average_relevance_score'], float)

@pytest.mark.asyncio
async def test_interactive_email_processing_integration(jd_agent):
    """Test the interactive email processing workflow."""
    
    # Mock email selection
    selected_emails = [SAMPLE_EMAIL_DATA]
    processed_jds = [{
        'job_description': JobDescription(
            role="Software Engineer",
            company="TechCorp",
            location="San Francisco, CA",
            experience_years=5,
            skills=["Python", "Django", "Flask", "AWS", "GCP"],
            content=SAMPLE_JD_TEXT,
            email_id=SAMPLE_EMAIL_DATA.get('id', 'test_id'),
            requirements=["5+ years of experience in Python development"],
            responsibilities=["Design and implement scalable backend services"]
        ),
        'email_data': SAMPLE_EMAIL_DATA
    }]
    
    with patch.object(jd_agent.email_selector, 'fetch_and_display_emails') as mock_fetch:
        mock_fetch.return_value = selected_emails
        
        with patch.object(jd_agent.email_selector, 'process_selected_emails') as mock_process:
            mock_process.return_value = processed_jds
            
            # Run interactive processing
            results = await jd_agent.process_emails_interactively(max_emails=1)
            
            # Verify results
            assert 'total_questions' in results
            assert 'export_files' in results
            assert 'processed_jds' in results
            assert results['processed_jds'] == 1
            assert len(results['export_files']) > 0

def test_configuration_validation(jd_agent):
    """Test the configuration validation."""
    
    # Test valid configuration
    assert jd_agent.validate_configuration() is True
    
    # Test invalid configuration
    with patch.object(jd_agent.config, 'OPENAI_API_KEY', None):
        assert jd_agent.validate_configuration() is False

if __name__ == '__main__':
    pytest.main(['-v', __file__])