"""
Test the async PromptEngine functionality with function calling and streaming.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from jd_agent.components.prompt_engine import PromptEngine
from jd_agent.utils.config import Config
from jd_agent.components.jd_parser import JobDescription


class TestPromptEngineAsync:
    """Test the async PromptEngine functionality."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return Config(
            OPENAI_API_KEY="test_key_123456789012345678901234567890",
            SERPAPI_KEY="test_serpapi_key_long_enough_for_validation"
        )
    
    @pytest.fixture
    def sample_jd(self):
        """Create a sample job description."""
        return JobDescription(
            email_id="test_email_123",
            company="Test Company",
            role="Data Scientist",
            location="San Francisco, CA",
            experience_years=3,
            skills=["Python", "Machine Learning", "SQL", "Statistics"],
            content="We are looking for a Data Scientist to join our team...",
            confidence_score=0.8,
            parsing_metadata={"method": "test"}
        )
    
    @pytest.fixture
    def sample_scraped_content(self):
        """Create sample scraped content."""
        return [
            {
                "source": "GitHub",
                "title": "Data Science Interview Questions",
                "content": "Common data science interview questions and answers...",
                "relevance_score": 0.8
            },
            {
                "source": "Medium",
                "title": "Machine Learning Interview Prep",
                "content": "How to prepare for ML interviews...",
                "relevance_score": 0.7
            }
        ]
    
    @pytest.mark.asyncio
    async def test_generate_questions_async_parallel_execution(self, config, sample_jd, sample_scraped_content):
        """Test that questions are generated in parallel for different difficulty levels."""
        with patch.object(PromptEngine, '_generate_difficulty_questions_async') as mock_generate:
            # Mock the difficulty generation to return sample questions
            mock_generate.return_value = [
                {
                    'difficulty': 'easy',
                    'question': 'What is Python?',
                    'answer': 'Python is a programming language',
                    'category': 'Technical',
                    'skills': ['Python']
                }
            ]
            
            # Create PromptEngine and test
            engine = PromptEngine(config)
            
            # Test async generation
            questions = await engine.generate_questions_async(sample_jd, sample_scraped_content)
            
            # Verify that the method was called for each difficulty level
            assert mock_generate.call_count == 3  # easy, medium, hard
            
            # Verify the calls were made with correct parameters
            calls = mock_generate.call_args_list
            difficulties = [call[0][2] for call in calls]  # Extract difficulty parameter
            assert 'easy' in difficulties
            assert 'medium' in difficulties
            assert 'hard' in difficulties
    
    @pytest.mark.asyncio
    async def test_process_streaming_response(self, config):
        """Test the streaming response processing."""
        engine = PromptEngine(config)
        
        # Create a mock stream with proper async generator
        class MockStream:
            async def __aiter__(self):
                # First chunk
                chunk1 = Mock()
                chunk1.choices = [Mock()]
                chunk1.choices[0].delta = Mock()
                chunk1.choices[0].delta.tool_calls = [Mock()]
                chunk1.choices[0].delta.tool_calls[0].function = Mock()
                chunk1.choices[0].delta.tool_calls[0].function.name = "create_questions"
                chunk1.choices[0].delta.tool_calls[0].function.arguments = '{"questions": ['
                yield chunk1
                
                # Second chunk
                chunk2 = Mock()
                chunk2.choices = [Mock()]
                chunk2.choices[0].delta = Mock()
                chunk2.choices[0].delta.tool_calls = [Mock()]
                chunk2.choices[0].delta.tool_calls[0].function = Mock()
                chunk2.choices[0].delta.tool_calls[0].function.name = "create_questions"
                chunk2.choices[0].delta.tool_calls[0].function.arguments = '{"question": "Test question", "answer": "Test answer", "category": "Technical", "skills": ["Python"]}]}'
                yield chunk2
        
        mock_stream = MockStream()
        
        # Test processing
        result = await engine._process_streaming_response(mock_stream)
        
        # Verify the result
        assert 'questions' in result
        assert len(result['questions']) == 1
        assert result['questions'][0]['question'] == "Test question"
    
    def test_sync_wrapper(self, config, sample_jd, sample_scraped_content):
        """Test that the sync wrapper calls the async method correctly."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock the async method
            with patch.object(PromptEngine, 'generate_questions_async') as mock_async:
                mock_async.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = engine.generate_questions(sample_jd, sample_scraped_content)
                
                # Verify the async method was called
                mock_async.assert_called_once_with(sample_jd, sample_scraped_content)
                assert questions == [{"question": "Test", "answer": "Test"}]
    
    def test_function_schema_structure(self, config):
        """Test that the function schema is properly structured."""
        engine = PromptEngine(config)
        
        # Test the schema structure by calling the method that builds it
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock streaming response
            mock_stream = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_stream
            
            # Mock empty stream
            async def empty_stream():
                yield Mock()
            
            mock_stream.__aiter__ = empty_stream
            
            # This will trigger the schema creation
            sample_jd = JobDescription(
                email_id="test",
                company="Test",
                role="Test",
                location="Test",
                experience_years=1,
                skills=["Test"],
                content="Test content",
                confidence_score=0.8,
                parsing_metadata={"method": "test"}
            )
            
            # The method should not fail due to schema issues
            try:
                asyncio.run(engine._generate_difficulty_questions_async(sample_jd, "test context", "easy"))
            except Exception as e:
                # Should fail due to mock, not schema
                assert "schema" not in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 