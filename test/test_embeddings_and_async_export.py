"""
Test embeddings functionality and async export features.
"""

import pytest
import asyncio
import tempfile
import os
import aiofiles
from unittest.mock import Mock, patch, AsyncMock
from jd_agent.components.question_bank import QuestionBank
from jd_agent.components.jd_parser import JobDescription
from jd_agent.utils.embeddings import EmbeddingManager, get_embedding_manager, compute_similarity
from jd_agent.utils.config import Config


class TestEmbeddings:
    """Test embeddings functionality."""
    
    @pytest.fixture
    def embedding_manager(self):
        return EmbeddingManager()
    
    def test_embedding_manager_initialization(self, embedding_manager):
        """Test embedding manager initialization."""
        assert embedding_manager.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert embedding_manager.embedding_cache == {}
    
    def test_get_embedding_manager_singleton(self):
        """Test that get_embedding_manager returns a singleton."""
        manager1 = get_embedding_manager()
        manager2 = get_embedding_manager()
        assert manager1 is manager2
    
    def test_embedding_cache(self, embedding_manager):
        """Test embedding caching functionality."""
        text = "What is Python?"
        
        # First call should generate embedding
        embedding1 = embedding_manager.get_embedding(text)
        assert embedding1 is not None
        assert embedding1.shape[0] > 0  # Should have some dimensions
        
        # Second call should use cache
        embedding2 = embedding_manager.get_embedding(text)
        assert embedding2 is not None
        assert embedding1.shape == embedding2.shape
        
        # Check cache size
        assert embedding_manager.get_cache_size() == 1
    
    def test_compute_similarity(self, embedding_manager):
        """Test similarity computation."""
        text1 = "What is Python?"
        text2 = "Can you explain what Python is?"
        text3 = "How do you implement a binary search?"
        
        # Similar texts should have higher similarity
        similarity_similar = embedding_manager.compute_similarity(text1, text2)
        similarity_different = embedding_manager.compute_similarity(text1, text3)
        
        assert 0.0 <= similarity_similar <= 1.0
        assert 0.0 <= similarity_different <= 1.0
        assert similarity_similar > similarity_different
    
    def test_compute_similarity_empty_strings(self, embedding_manager):
        """Test similarity computation with empty strings."""
        similarity1 = embedding_manager.compute_similarity("", "What is Python?")
        similarity2 = embedding_manager.compute_similarity("What is Python?", "")
        similarity3 = embedding_manager.compute_similarity("", "")
        
        assert similarity1 == 0.0
        assert similarity2 == 0.0
        assert similarity3 == 0.0
    
    def test_clear_cache(self, embedding_manager):
        """Test cache clearing functionality."""
        # Add some embeddings to cache
        embedding_manager.get_embedding("Test text 1")
        embedding_manager.get_embedding("Test text 2")
        
        assert embedding_manager.get_cache_size() == 2
        
        # Clear cache
        embedding_manager.clear_cache()
        assert embedding_manager.get_cache_size() == 0
    
    def test_global_functions(self):
        """Test global embedding functions."""
        text = "What is Python?"
        
        # Test get_embedding
        embedding = get_embedding_manager().get_embedding(text)
        assert embedding is not None
        
        # Test compute_similarity
        similarity = compute_similarity("What is Python?", "Can you explain Python?")
        assert 0.0 <= similarity <= 1.0


class TestAsyncExport:
    """Test async export functionality."""
    
    @pytest.fixture
    def question_bank(self):
        config = Config()
        return QuestionBank(config)
    
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
    
    @pytest.mark.asyncio
    async def test_export_questions_async(self, question_bank, sample_jd, sample_questions):
        """Test async export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override export directory
            question_bank.export_dir = temp_dir
            
            # Test async export
            export_files = await question_bank.export_questions_async(
                sample_jd, sample_questions, ['markdown', 'csv', 'json']
            )
            
            # Check that files were created
            assert 'markdown' in export_files
            assert 'csv' in export_files
            assert 'json' in export_files
            
            # Check that files exist
            for format_type, file_path in export_files.items():
                assert os.path.exists(file_path)
                assert os.path.getsize(file_path) > 0
    
    @pytest.mark.asyncio
    async def test_export_markdown_async(self, question_bank, sample_jd, sample_questions):
        """Test async markdown export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            question_bank.export_dir = temp_dir
            
            file_path = await question_bank._export_markdown_async(
                sample_questions, sample_jd, "test_export"
            )
            
            assert os.path.exists(file_path)
            
            # Read and verify content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            assert "Interview Questions for Test Company" in content
            assert "What is Python?" in content
            assert "How do you implement a binary search?" in content
            assert "Easy Questions" in content
            assert "Medium Questions" in content
    
    @pytest.mark.asyncio
    async def test_export_csv_async(self, question_bank, sample_jd, sample_questions):
        """Test async CSV export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            question_bank.export_dir = temp_dir
            
            file_path = await question_bank._export_csv_async(
                sample_questions, sample_jd, "test_export"
            )
            
            assert os.path.exists(file_path)
            
            # Read and verify content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            lines = content.strip().split('\n')
            assert len(lines) == 3  # Header + 2 data rows
            
            # Check header
            assert "difficulty,question,answer,category,skills,source,relevance_score,company,role" in lines[0]
            
            # Check data rows
            assert "easy" in lines[1]
            assert "medium" in lines[2]
            assert "Python" in lines[1]
            assert "Algorithms" in lines[2]
    
    @pytest.mark.asyncio
    async def test_export_json_async(self, question_bank, sample_jd, sample_questions):
        """Test async JSON export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            question_bank.export_dir = temp_dir
            
            file_path = await question_bank._export_json_async(
                sample_questions, sample_jd, "test_export"
            )
            
            assert os.path.exists(file_path)
            
            # Read and verify content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            import json
            data = json.loads(content)
            
            # Check metadata
            assert data['metadata']['company'] == "Test Company"
            assert data['metadata']['role'] == "Software Engineer"
            assert data['metadata']['total_questions'] == 2
            
            # Check questions
            assert len(data['questions']) == 2
            assert data['questions'][0]['difficulty'] == 'easy'
            assert data['questions'][1]['difficulty'] == 'medium'
    
    def test_export_questions_sync_fallback(self, question_bank, sample_jd, sample_questions):
        """Test sync fallback when not in async context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            question_bank.export_dir = temp_dir
            
            # This should use sync fallback
            export_files = question_bank.export_questions_sync(
                sample_jd, sample_questions, ['markdown']
            )
            
            assert 'markdown' in export_files
            assert os.path.exists(export_files['markdown'])
    
    @pytest.mark.asyncio
    async def test_export_questions_async_context(self, question_bank, sample_jd, sample_questions):
        """Test export_questions in async context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            question_bank.export_dir = temp_dir
            
            # This should detect async context and use async version
            export_files = await question_bank.export_questions(
                sample_jd, sample_questions, ['json']
            )
            
            assert 'json' in export_files
            assert os.path.exists(export_files['json'])
    
    def test_export_questions_error_handling(self, question_bank, sample_jd, sample_questions):
        """Test error handling in export functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            question_bank.export_dir = temp_dir
            
            # Test with invalid format
            export_files = question_bank.export_questions_sync(
                sample_jd, sample_questions, ['invalid_format']
            )
            
            # Should handle error gracefully and return empty dict
            assert export_files == {}


class TestEmbeddingRelevanceScoring:
    """Test embedding-based relevance scoring."""
    
    @pytest.fixture
    def question_bank(self):
        config = Config()
        return QuestionBank(config)
    
    @pytest.fixture
    def sample_jd(self):
        return JobDescription(
            email_id="test_email_123",
            company="Tech Corp",
            role="Python Developer",
            location="San Francisco, CA",
            experience_years=3,
            skills=["Python", "Django", "PostgreSQL", "REST APIs"],
            content="We are looking for a Python Developer...",
            confidence_score=0.8,
            parsing_metadata={"method": "test"}
        )
    
    def test_calculate_relevance_score_with_embeddings(self, question_bank, sample_jd):
        """Test relevance scoring with embeddings."""
        # Question highly relevant to JD
        relevant_question = {
            'difficulty': 'medium',
            'question': 'How do you implement REST APIs in Django?',
            'answer': 'Django REST framework provides tools for building APIs.',
            'category': 'Technical',
            'skills': ['Python', 'Django', 'REST APIs']
        }
        
        # Question less relevant to JD
        less_relevant_question = {
            'difficulty': 'easy',
            'question': 'What is machine learning?',
            'answer': 'Machine learning is a subset of artificial intelligence.',
            'category': 'Technical',
            'skills': ['Machine Learning']
        }
        
        # Calculate scores
        relevant_score = question_bank._calculate_relevance_score(relevant_question, sample_jd)
        less_relevant_score = question_bank._calculate_relevance_score(less_relevant_question, sample_jd)
        
        # Relevant question should have higher score
        assert relevant_score > less_relevant_score
        assert 0.0 <= relevant_score <= 1.0
        assert 0.0 <= less_relevant_score <= 1.0
    
    def test_calculate_relevance_score_skill_matching(self, question_bank, sample_jd):
        """Test relevance scoring with skill matching."""
        # Question with matching skills
        matching_question = {
            'difficulty': 'easy',
            'question': 'What is Python?',
            'answer': 'Python is a programming language.',
            'category': 'Technical',
            'skills': ['Python', 'Django']
        }
        
        # Question with non-matching skills
        non_matching_question = {
            'difficulty': 'easy',
            'question': 'What is JavaScript?',
            'answer': 'JavaScript is a programming language.',
            'category': 'Technical',
            'skills': ['JavaScript', 'React']
        }
        
        # Calculate scores
        matching_score = question_bank._calculate_relevance_score(matching_question, sample_jd)
        non_matching_score = question_bank._calculate_relevance_score(non_matching_question, sample_jd)
        
        # Matching question should have higher score
        assert matching_score > non_matching_score
    
    def test_calculate_relevance_score_experience_matching(self, question_bank, sample_jd):
        """Test relevance scoring with experience level matching."""
        # Question matching experience level
        matching_question = {
            'difficulty': 'medium',  # Matches 3 years experience
            'question': 'How do you optimize database queries?',
            'answer': 'Use indexes, avoid N+1 queries, and optimize SQL.',
            'category': 'Technical',
            'skills': ['PostgreSQL']
        }
        
        # Question not matching experience level
        non_matching_question = {
            'difficulty': 'hard',  # Doesn't match 3 years experience
            'question': 'How do you design a distributed system?',
            'answer': 'Use microservices, load balancing, and caching.',
            'category': 'Technical',
            'skills': ['System Design']
        }
        
        # Calculate scores
        matching_score = question_bank._calculate_relevance_score(matching_question, sample_jd)
        non_matching_score = question_bank._calculate_relevance_score(non_matching_question, sample_jd)
        
        # Matching question should have higher score
        assert matching_score > non_matching_score
    
    def test_calculate_relevance_score_embedding_fallback(self, question_bank, sample_jd):
        """Test relevance scoring when embeddings fail."""
        question = {
            'difficulty': 'easy',
            'question': 'What is Python?',
            'answer': 'Python is a programming language.',
            'category': 'Technical',
            'skills': ['Python']
        }
        
        # Mock embedding failure
        with patch('jd_agent.components.question_bank.compute_similarity') as mock_similarity:
            mock_similarity.side_effect = Exception("Embedding error")
            
            # Should still calculate score using traditional logic
            score = question_bank._calculate_relevance_score(question, sample_jd)
            
            assert 0.0 <= score <= 1.0
            assert score > 0.0  # Should have some score from traditional logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 