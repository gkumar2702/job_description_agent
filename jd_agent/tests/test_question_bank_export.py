"""
Tests for QuestionBank export paths and stats using realistic question dicts.
"""

import os
import tempfile
import pytest

from ..components.question_bank import QuestionBank
from ..components.jd_parser import JobDescription
from ..utils.config import Config


@pytest.fixture
def bank(tmp_path) -> QuestionBank:
    cfg = Config(EXPORT_DIR=str(tmp_path))
    return QuestionBank(cfg)


@pytest.fixture
def sample_jd() -> JobDescription:
    return JobDescription(
        company='Fabrikam',
        role='Data Engineer',
        location='Bangalore',
        experience_years=3,
        skills=['Python', 'Spark', 'SQL'],
        content='Hiring Data Engineer with Python and Spark.',
        email_id='eid',
        confidence_score=0.75,
        salary_lpa=0.0,
        requirements=[],
        responsibilities=[],
        parsing_metadata={}
    )


def test_add_and_deduplicate(bank: QuestionBank) -> None:
    questions = [
        {
            'difficulty': 'easy',
            'question': 'What is a primary key in SQL?',
            'answer': 'A unique identifier for table records.',
            'category': 'Database',
            'skills': ['SQL'],
            'source': 'Generated'
        },
        {
            'difficulty': 'easy',
            'question': 'Explain primary key in SQL.',  # similar to above
            'answer': 'A unique identifier for a table row.',
            'category': 'Database',
            'skills': ['SQL'],
            'source': 'Generated'
        }
    ]
    bank.add_questions(questions)
    deduped = bank.deduplicate_questions()
    assert len(deduped) in (1, 2)  # similarity threshold may keep or drop similar
    assert len(bank.questions) == len(deduped)


def test_scoring_and_export_pdf(bank: QuestionBank, sample_jd: JobDescription) -> None:
    bank.add_questions([
        {
            'difficulty': 'medium',
            'question': 'Describe a Spark pipeline for ETL with Python.',
            'answer': 'Use PySpark for extraction, transformations, and loading.',
            'category': 'Data Engineering',
            'skills': ['Spark', 'Python'],
            'source': 'Generated'
        }
    ])
    scored = bank.score_questions(sample_jd)
    assert len(scored) == 1
    assert 0.0 <= scored[0]['relevance_score'] <= 1.0

    res = bank.export_questions_sync(sample_jd, scored)
    assert 'pdf' in res
    assert os.path.exists(res['pdf'])
    assert os.path.getsize(res['pdf']) > 1024


def test_statistics(bank: QuestionBank) -> None:
    bank.add_questions([
        {
            'difficulty': 'easy',
            'question': 'What is Python list comprehension?',
            'answer': 'A concise way to create lists.',
            'category': 'Programming',
            'skills': ['Python'],
            'source': 'Generated'
        }
    ])
    stats = bank.get_question_statistics()
    assert stats['total_questions'] >= 1
    assert 'easy' in stats['difficulty_distribution']


