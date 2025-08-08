"""
Performance tests for JD Agent components.
"""

import time
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from jd_agent.utils.config import Config
from jd_agent.main import JDAgent
from jd_agent.components.jd_parser import JobDescription

# Sample test data (same as integration tests)
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
def config():
    """Create a test configuration."""
    config = Config()
    config.OPENAI_API_KEY = 'test-key'
    config.SERPAPI_KEY = 'test-key'
    config.DATABASE_PATH = ':memory:'
    config.OPENAI_MODEL = "gpt-3.5-turbo"
    config.MAX_TOKENS = 500
    config.TEMPERATURE = 0.0
    return config

@pytest.fixture
def jd_agent(config):
    """Create a JDAgent instance with test configuration."""
    return JDAgent(config)

async def measure_time(func, *args, **kwargs):
    """Measure execution time of an async function."""
    start_time = time.time()
    result = await func(*args, **kwargs)
    end_time = time.time()
    duration = end_time - start_time
    return result, duration

@pytest.mark.asyncio
async def test_component_performance(jd_agent):
    """Test performance of individual components."""
    
    print("\nComponent Performance Analysis:")
    print("=" * 50)
    
    # 1. Test JD Parser Performance
    start_time = time.time()
    jd = jd_agent.jd_parser.parse_job_description(SAMPLE_JD_TEXT, "TechCorp")
    parser_duration = time.time() - start_time
    print(f"1. JD Parser: {parser_duration:.2f} seconds")
    
    # 2. Test Scraping Agent Performance
    start_time = time.time()
    scraped_content = jd_agent.scraping_agent.run_scraping_workflow(jd)
    scraping_duration = time.time() - start_time
    print(f"2. Scraping Agent: {scraping_duration:.2f} seconds")
    
    # 3. Test Question Generation Performance
    start_time = time.time()
    questions = await jd_agent.prompt_engine.generate_questions_async(jd, scraped_content.get('content', []))
    question_gen_duration = time.time() - start_time
    print(f"3. Question Generation: {question_gen_duration:.2f} seconds")
    
    # 4. Test PDF Export Performance
    start_time = time.time()
    metadata = {
        'email_subject': SAMPLE_EMAIL_DATA.get('subject', 'Unknown'),
        'email_sender': SAMPLE_EMAIL_DATA.get('from', 'Unknown'),
        'email_date': SAMPLE_EMAIL_DATA.get('date', 'Unknown'),
        'total_questions': len(questions),
        'questions_by_difficulty': {},
        'average_relevance_score': 0.0
    }
    pdf_path = jd_agent.pdf_exporter.export_questions_to_pdf(jd, questions, metadata)
    export_duration = time.time() - start_time
    print(f"4. PDF Export: {export_duration:.2f} seconds")
    
    # 5. Test Full Pipeline Performance
    start_time = time.time()
    results = await jd_agent.process_single_jd(SAMPLE_JD_TEXT, "TechCorp")
    pipeline_duration = time.time() - start_time
    print(f"5. Full Pipeline: {pipeline_duration:.2f} seconds")
    
    print("\nComponents Taking > 2 minutes:")
    print("-" * 50)
    for component, duration in [
        ("JD Parser", parser_duration),
        ("Scraping Agent", scraping_duration),
        ("Question Generation", question_gen_duration),
        ("PDF Export", export_duration),
        ("Full Pipeline", pipeline_duration)
    ]:
        if duration > 120:  # 2 minutes
            print(f"- {component}: {duration:.2f} seconds")

if __name__ == '__main__':
    pytest.main(['-v', __file__])