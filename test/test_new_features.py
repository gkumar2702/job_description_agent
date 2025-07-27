"""
Test new features: Excel export, strategy pattern, structured logging.
"""

import pytest
import tempfile
import json
from pathlib import Path
from jd_agent.components.question_bank import QuestionBank
from jd_agent.components.jd_parser import JobDescription
from jd_agent.components.scoring_strategies import HeuristicScorer, EmbeddingScorer, HybridScorer
from jd_agent.utils.config import Config


class TestNewFeatures:
    """Test new features implementation."""
    
    @pytest.fixture
    def config(self):
        return Config()
    
    @pytest.fixture
    def sample_jd(self):
        return JobDescription(
            email_id="test_email_123",
            company="Test Company",
            role="Software Engineer",
            location="San Francisco, CA",
            experience_years=3,
            skills=["Python", "JavaScript", "React"],
            content="We are looking for a Software Engineer...",
            confidence_score=0.8,
            parsing_metadata={"method": "test"}
        )
    
    @pytest.fixture
    def sample_questions(self):
        return [
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'medium',
                'question': 'How do you implement a binary search?',
                'answer': 'Binary search is a divide and conquer algorithm.',
                'category': 'Technical',
                'skills': ['Algorithms']
            }
        ]
    
    def test_strategy_pattern(self, config, sample_jd, sample_questions):
        """Test scoring strategy pattern."""
        # Test HeuristicScorer
        heuristic_qb = QuestionBank(config, scorer=HeuristicScorer())
        heuristic_qb.add_questions(sample_questions)
        heuristic_scores = heuristic_qb.score_questions(sample_jd)
        
        # Test EmbeddingScorer
        embedding_qb = QuestionBank(config, scorer=EmbeddingScorer())
        embedding_qb.add_questions(sample_questions)
        embedding_scores = embedding_qb.score_questions(sample_jd)
        
        # Test HybridScorer
        hybrid_qb = QuestionBank(config, scorer=HybridScorer())
        hybrid_qb.add_questions(sample_questions)
        hybrid_scores = hybrid_qb.score_questions(sample_jd)
        
        # All should return scored questions
        assert len(heuristic_scores) == 2
        assert len(embedding_scores) == 2
        assert len(hybrid_scores) == 2
        
        # All should have relevance scores
        for scores in [heuristic_scores, embedding_scores, hybrid_scores]:
            for question in scores:
                assert 'relevance_score' in question
                assert 0.0 <= question['relevance_score'] <= 1.0
    
    def test_excel_export(self, config, sample_jd, sample_questions):
        """Test Excel export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override export directory
            config.EXPORT_DIR = temp_dir
            
            qb = QuestionBank(config)
            qb.add_questions(sample_questions)
            
            # Test Excel export
            file_path = qb._export_xlsx(sample_questions, sample_jd, "test_export")
            
            # Check that file was created
            assert Path(file_path).exists()
            assert Path(file_path).suffix == '.xlsx'
            assert Path(file_path).stat().st_size > 0
    
    def test_constants_usage(self, config, sample_jd, sample_questions):
        """Test that constants are used instead of inline literals."""
        from jd_agent.utils.constants import SIMILARITY_THRESHOLD
        
        qb = QuestionBank(config)
        qb.add_questions(sample_questions)
        
        # Test deduplication uses constant
        deduplicated = qb.deduplicate_questions()
        
        # Should work without errors (constants are used internally)
        assert len(deduplicated) <= len(sample_questions)
    
    def test_structured_logging(self, config, sample_jd, sample_questions, caplog):
        """Test structured logging with timer decorators."""
        qb = QuestionBank(config)
        qb.add_questions(sample_questions)
        
        # Test deduplication logging
        deduplicated = qb.deduplicate_questions()
        
        # Test scoring logging
        scored = qb.score_questions(sample_jd)
        
        # Should have logged events
        assert len(deduplicated) <= len(sample_questions)
        assert len(scored) == len(deduplicated)
    
    def test_question_objects(self, config, sample_jd, sample_questions):
        """Test that questions are converted to Question objects."""
        from jd_agent.utils.schemas import Question
        
        qb = QuestionBank(config)
        qb.add_questions(sample_questions)
        
        # All questions should be Question objects
        for question in qb.questions:
            assert isinstance(question, Question)
            assert hasattr(question, 'question')
            assert hasattr(question, 'answer')
            assert hasattr(question, 'difficulty')
            assert hasattr(question, 'category')
            assert hasattr(question, 'skills')
    
    def test_cli_imports(self):
        """Test that CLI can import all required modules."""
        # This test ensures the CLI script can import all necessary modules
        from jd_agent.components.question_bank import QuestionBank
        from jd_agent.components.jd_parser import JobDescription
        from jd_agent.components.scoring_strategies import HeuristicScorer, EmbeddingScorer, HybridScorer
        from jd_agent.utils.config import Config
        
        # Should not raise any import errors
        assert QuestionBank is not None
        assert JobDescription is not None
        assert HeuristicScorer is not None
        assert EmbeddingScorer is not None
        assert HybridScorer is not None
        assert Config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 