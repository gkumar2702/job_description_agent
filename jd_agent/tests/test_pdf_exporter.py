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

    def test_export_questions_formats_code_and_bullets_and_email(self, exporter: PDFExporter, sample_jd: JobDescription) -> None:
        questions = [
            {
                'difficulty': 'easy',
                'question': 'Write a Python function to add two numbers',
                'answer': 'Use a simple function.\n```python\ndef add(a: int, b: int) -> int:\n    return a + b\n```',
                'category': 'Python',
                'skills': ['Python']
            },
            {
                'difficulty': 'medium',
                'question': 'Write an SQL to find top 5 customers by revenue',
                'answer': 'You can aggregate and sort.\n```sql\nSELECT customer_id, SUM(amount) AS revenue\nFROM orders\nGROUP BY customer_id\nORDER BY revenue DESC\nLIMIT 5;\n```',
                'category': 'SQL',
                'skills': ['SQL']
            },
            {
                'difficulty': 'easy',
                'question': 'List steps for model evaluation',
                'answer': '- Split data into train/test\n- Choose metrics (AUC/Accuracy/F1)\n- Cross-validate\n- Analyze errors',
                'category': 'ML',
                'skills': ['ML']
            },
        ]
        metadata = {
            'email_subject': 'Hiring: Data Scientist - Python, SQL',
            'email_sender': 'recruiter@example.com',
            'email_date': '2025-01-01',
            'generated_by': 'unit-test'
        }

        pdf_path = exporter.export_questions_to_pdf(sample_jd, questions, metadata)
        assert os.path.exists(pdf_path)
        # With code blocks and lists, size should be reasonably larger
        assert os.path.getsize(pdf_path) > 2048

    def test_export_questions_handles_missing_email_info(self, exporter: PDFExporter, sample_jd: JobDescription) -> None:
        questions = [
            {
                'difficulty': 'easy',
                'question': 'Explain regularization',
                'answer': 'L1 and L2 regularization help prevent overfitting by penalizing large weights.',
                'category': 'ML',
                'skills': ['ML']
            }
        ]
        metadata = {
            # Intentionally omit email_* to ensure section is skipped gracefully
            'generated_by': 'unit-test'
        }

        pdf_path = exporter.export_questions_to_pdf(sample_jd, questions, metadata)
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1024


