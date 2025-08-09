"""
Tests for scoring strategies.
"""

import pytest
from unittest.mock import patch

from ..components.scoring_strategies import HeuristicScorer, EmbeddingScorer, HybridScorer
from ..components.jd_parser import JobDescription
from ..utils.schemas import Question


@pytest.fixture
def sample_jd() -> JobDescription:
    return JobDescription(
        company='Contoso',
        role='Software Engineer',
        location='Bengaluru',
        experience_years=4,
        skills=['Python', 'AWS', 'SQL'],
        content='JD content',
        email_id='email',
        confidence_score=0.7,
        salary_lpa=0.0,
        requirements=[],
      responsibilities=[],
        parsing_metadata={}
    )


def make_question(text: str, difficulty: str = 'medium', skills=None) -> Question:
    return Question(
        difficulty=difficulty,
        question=text,
        answer='answer',
        category='Technical',
        skills=skills or [],
        source='Generated'
    )


def test_heuristic_scorer_basic(sample_jd: JobDescription) -> None:
    scorer = HeuristicScorer()
    q = make_question('Explain Python decorators for AWS Lambda functions', skills=['Python', 'AWS'])
    score = scorer.score(q, sample_jd)
    assert 0.0 <= score <= 1.0
    # Expect a reasonable mid-to-high score due to skill and role keywords
    assert score >= 0.3


@patch('jd_agent.utils.embeddings.compute_similarity', return_value=0.65)
def test_embedding_scorer_mixed(mock_sim, sample_jd: JobDescription) -> None:
    scorer = EmbeddingScorer(embedding_weight=0.6, heuristic_weight=0.4)
    q = make_question('Describe a system using Python and AWS for data processing', skills=['Python'])
    score = scorer.score(q, sample_jd)
    assert 0.0 <= score <= 1.0
    # With embed 0.65 and some heuristic, expect > 0.4 realistically
    assert score >= 0.4


@patch('jd_agent.components.scoring_strategies.compute_similarity', return_value=0.7)
def test_hybrid_scorer_weights(mock_sim, sample_jd: JobDescription) -> None:
    scorer = HybridScorer(embedding_weight=0.5, heuristic_weight=0.5)
    q = make_question('What SQL indices would you create for login table?', skills=['SQL'])
    score = scorer.score(q, sample_jd)
    assert 0.0 <= score <= 1.0
    # Balanced weights with moderate-high similarity should be >= 0.3 realistically
    assert score >= 0.3


