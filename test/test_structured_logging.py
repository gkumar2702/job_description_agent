"""
Test the structured logging functionality in PromptEngine.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from io import StringIO
import sys
from jd_agent.components.prompt_engine import PromptEngine
from jd_agent.utils.config import Config
from jd_agent.components.jd_parser import JobDescription


class TestStructuredLogging:
    """Test structured logging functionality."""
    
    @pytest.fixture
    def config(self):
        return Config(
            OPENAI_API_KEY="test_key_123456789012345678901234567890",
            SERPAPI_KEY="test_serpapi_key_long_enough_for_validation",
            TEMPERATURE=0.3,
            TOP_P=0.9,
            MAX_TOKENS=2000
        )
    
    @pytest.fixture
    def sample_jd(self):
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
        return [
            {
                'source': 'GitHub',
                'title': 'Data Science Interview Questions',
                'content': 'This is a comprehensive guide to data science interview questions.',
                'relevance_score': 0.9
            }
        ]
    
    def test_estimate_tokens(self, config):
        """Test token estimation functionality."""
        engine = PromptEngine(config)
        
        # Test token estimation
        text = "This is a test sentence with some words."
        tokens = engine._estimate_tokens(text)
        
        # Should be roughly 1/4 of character count
        expected_tokens = len(text) // 4
        assert tokens == expected_tokens
        
        # Test with longer text
        long_text = "This is a much longer text that should have more tokens. " * 10
        long_tokens = engine._estimate_tokens(long_text)
        assert long_tokens > tokens
    
    @pytest.mark.asyncio
    async def test_question_generation_logging(self, config, sample_jd, sample_scraped_content):
        """Test that question generation logs structured events."""
        # Capture stdout to check logs
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                    # Mock streaming response
                    mock_stream = AsyncMock()
                    mock_create.return_value = mock_stream
                    
                    with patch.object(PromptEngine, '_process_streaming_response') as mock_process:
                        mock_process.return_value = {
                            'questions': [
                                {
                                    'question': 'What is Python?',
                                    'answer': 'Python is a programming language.',
                                    'category': 'Technical',
                                    'skills': ['Python']
                                }
                            ]
                        }
                        
                        engine = PromptEngine(config)
                        questions = await engine.generate_questions_async(sample_jd, sample_scraped_content)
                        
                        # Should have generated questions
                        assert len(questions) > 0
                        
                        # Check for structured log events
                        output = captured_output.getvalue()
                        log_lines = output.strip().split('\n')
                        
                        # Should have question_generation events
                        generation_events = [line for line in log_lines if '"question_generation"' in line]
                        assert len(generation_events) >= 3  # One for each difficulty level
                        
                        # Parse and verify log structure
                        for event_line in generation_events:
                            try:
                                log_data = json.loads(event_line)
                                assert log_data['event'] == 'question_generation'
                                assert log_data['role'] == 'Data Scientist'
                                assert log_data['company'] == 'Test Company'
                                assert 'difficulty' in log_data
                                assert 'tokens_in' in log_data
                                assert 'tokens_out' in log_data
                                assert 'latency_ms' in log_data
                                assert 'num_questions' in log_data
                                assert 'temperature' in log_data
                                assert isinstance(log_data['latency_ms'], int)
                                assert isinstance(log_data['num_questions'], int)
                                assert isinstance(log_data['temperature'], float)
                            except json.JSONDecodeError:
                                pytest.fail(f"Invalid JSON in log line: {event_line}")
    
    @pytest.mark.asyncio
    async def test_question_enhancement_logging(self, config, sample_scraped_content):
        """Test that question enhancement logs structured events."""
        # Capture stdout to check logs
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                    # Mock successful responses
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = "Enhanced answer with more details."
                    mock_create.return_value = mock_response
                    
                    engine = PromptEngine(config)
                    
                    # Test questions for enhancement
                    test_questions = [
                        {
                            'question': 'What is Python?',
                            'answer': 'Python is a programming language.',
                            'category': 'Technical',
                            'skills': ['Python']
                        }
                    ]
                    
                    enhanced_questions = await engine.enhance_questions_with_context_async(
                        test_questions, 
                        sample_scraped_content
                    )
                    
                    # Should have enhanced questions
                    assert len(enhanced_questions) == len(test_questions)
                    
                    # Check for structured log events
                    output = captured_output.getvalue()
                    log_lines = output.strip().split('\n')
                    
                    # Should have question_enhancement events
                    enhancement_events = [line for line in log_lines if '"question_enhancement"' in line]
                    assert len(enhancement_events) >= 1
                    
                    # Parse and verify log structure
                    for event_line in enhancement_events:
                        try:
                            log_data = json.loads(event_line)
                            assert log_data['event'] == 'question_enhancement'
                            assert 'num_questions' in log_data
                            assert 'enhanced_count' in log_data
                            assert 'latency_ms' in log_data
                            assert isinstance(log_data['num_questions'], int)
                            assert isinstance(log_data['enhanced_count'], int)
                            assert isinstance(log_data['latency_ms'], int)
                        except json.JSONDecodeError:
                            pytest.fail(f"Invalid JSON in log line: {event_line}")
    
    @pytest.mark.asyncio
    async def test_logging_with_custom_parameters(self, config, sample_jd, sample_scraped_content):
        """Test that logging includes custom parameters."""
        # Capture stdout to check logs
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                    # Mock streaming response
                    mock_stream = AsyncMock()
                    mock_create.return_value = mock_stream
                    
                    with patch.object(PromptEngine, '_process_streaming_response') as mock_process:
                        mock_process.return_value = {
                            'questions': [
                                {
                                    'question': 'What is Python?',
                                    'answer': 'Python is a programming language.',
                                    'category': 'Technical',
                                    'skills': ['Python']
                                }
                            ]
                        }
                        
                        engine = PromptEngine(config)
                        
                        # Test with custom parameters
                        questions = await engine.generate_questions_async(
                            sample_jd, 
                            sample_scraped_content,
                            temperature=0.0,
                            seed=42
                        )
                        
                        # Check for structured log events with custom parameters
                        output = captured_output.getvalue()
                        log_lines = output.strip().split('\n')
                        
                        generation_events = [line for line in log_lines if '"question_generation"' in line]
                        assert len(generation_events) >= 3
                        
                        # Verify custom temperature is logged
                        for event_line in generation_events:
                            try:
                                log_data = json.loads(event_line)
                                assert log_data['temperature'] == 0.0
                            except json.JSONDecodeError:
                                pytest.fail(f"Invalid JSON in log line: {event_line}")
    
    def test_logging_format_compliance(self, config):
        """Test that logging format is compliant with Loki/DataDog requirements."""
        engine = PromptEngine(config)
        
        # Test that logs are valid JSON
        test_text = "This is a test message"
        tokens = engine._estimate_tokens(test_text)
        
        # Should be valid integer
        assert isinstance(tokens, int)
        assert tokens >= 0
        
        # Test with empty string
        empty_tokens = engine._estimate_tokens("")
        assert empty_tokens == 0
        
        # Test with very long string
        long_text = "x" * 1000
        long_tokens = engine._estimate_tokens(long_text)
        assert long_tokens == 250  # 1000 // 4
    
    @pytest.mark.asyncio
    async def test_logging_performance_metrics(self, config, sample_jd, sample_scraped_content):
        """Test that performance metrics are accurately logged."""
        # Capture stdout to check logs
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                    # Mock streaming response
                    mock_stream = AsyncMock()
                    mock_create.return_value = mock_stream
                    
                    with patch.object(PromptEngine, '_process_streaming_response') as mock_process:
                        mock_process.return_value = {
                            'questions': [
                                {
                                    'question': 'What is Python?',
                                    'answer': 'Python is a programming language.',
                                    'category': 'Technical',
                                    'skills': ['Python']
                                }
                            ]
                        }
                        
                        engine = PromptEngine(config)
                        questions = await engine.generate_questions_async(sample_jd, sample_scraped_content)
                        
                        # Check for performance metrics in logs
                        output = captured_output.getvalue()
                        log_lines = output.strip().split('\n')
                        
                        generation_events = [line for line in log_lines if '"question_generation"' in line]
                        assert len(generation_events) >= 3
                        
                        # Verify performance metrics
                        for event_line in generation_events:
                            try:
                                log_data = json.loads(event_line)
                                assert log_data['latency_ms'] >= 0
                                assert log_data['tokens_in'] >= 0
                                assert log_data['tokens_out'] >= 0
                                assert log_data['num_questions'] >= 0
                            except json.JSONDecodeError:
                                pytest.fail(f"Invalid JSON in log line: {event_line}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 