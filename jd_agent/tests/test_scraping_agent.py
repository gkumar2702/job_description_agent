"""
Tests for ScrapingAgent high-level orchestration with realistic expectations.
"""

import pytest
from unittest.mock import Mock

# Skip these tests if langgraph is not installed (optional dependency)
pytest.importorskip("langgraph")

from ..components.scraping_agent import ScrapingAgent, ScrapingState
from ..components.jd_parser import JobDescription
from ..utils.config import Config
from ..utils.database import Database


@pytest.fixture
def agent() -> ScrapingAgent:
    cfg = Config()
    db = Database(":memory:")
    return ScrapingAgent(cfg, db)


@pytest.fixture
def sample_jd() -> JobDescription:
    return JobDescription(
        company='Globex',
        role='Software Engineer',
        location='Bengaluru',
        experience_years=3,
        skills=['Python', 'Algorithms', 'Data Structures'],
        content='We are hiring Software Engineers.',
        email_id='e1',
        confidence_score=0.8,
        salary_lpa=0.0,
        requirements=[],
        responsibilities=[],
        parsing_metadata={}
    )


def test_run_scraping_workflow_returns_mock(agent: ScrapingAgent, sample_jd: JobDescription) -> None:
    results = agent.run_scraping_workflow(sample_jd)
    assert results['success'] is True
    assert results['content_count'] >= 1
    assert isinstance(results['content'], list)


def test_get_usage_stats(agent: ScrapingAgent) -> None:
    stats = agent.get_usage_stats()
    # Realistic keys with integer/boolean values
    assert 'serpapi_calls' in stats
    assert 'max_serpapi_calls' in stats
    assert 'scraping_methods' in stats
    assert isinstance(stats['serpapi_calls'], int)


