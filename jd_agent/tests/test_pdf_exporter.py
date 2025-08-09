"""
Tests for PDFExporter component.
"""

import os
import tempfile
from pathlib import Path
import pytest

from ..components.pdf_exporter import PDFExporter
from ..components.jd_parser import JobDescription


class TestPDFExporter:
    @pytest.fixture
    def exporter(self) -> PDFExporter:
        with tempfile.TemporaryDirectory() as tmp:
            exp = PDFExporter(export_dir=tmp)
            yield exp

    @pytest.fixture
    def sample_jd(self) -> JobDescription:
        return JobDescription(
            company='Acme Corp',
            role='Data Scientist',
            location='Bengaluru',
            experience_years=5,
            skills=['Python', 'Pandas', 'ML'],
            content='We are hiring a Data Scientist with experience in ML and Python.',
            email_id='email_id_123',
            confidence_score=0.82,
            salary_lpa=0.0,
            requirements=[],
            responsibilities=[],
            parsing_metadata={}
        )

    def test_export_questions_to_pdf_creates_file(self, exporter: PDFExporter, sample_jd: JobDescription) -> None:
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is overfitting in machine learning?',
                'answer': 'Overfitting occurs when a model learns noise instead of signal.',
                'category': 'ML',
                'skills': ['ML']
            },
            {
                'difficulty': 'medium',
                'question': 'Explain the bias-variance tradeoff.',
                'answer': 'It represents a balance between model complexity and generalization.',
                'category': 'ML',
                'skills': ['ML']
            },
        ]
        metadata = {
            'pipeline': 'test',
            'generated_by': 'unit-test'
        }

        pdf_path = exporter.export_questions_to_pdf(sample_jd, questions, metadata)
        assert os.path.exists(pdf_path)
        # Basic size check: non-empty PDF, typically > 1KB
        assert os.path.getsize(pdf_path) > 1024


