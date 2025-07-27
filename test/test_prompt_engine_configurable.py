"""
Test the configurable parameters functionality in PromptEngine.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from jd_agent.components.prompt_engine import PromptEngine
from jd_agent.utils.config import Config
from jd_agent.components.jd_parser import JobDescription


class TestPromptEngineConfigurable:
    """Test configurable parameters in PromptEngine."""
    
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
    
    def test_generate_questions_with_default_parameters(self, config, sample_jd, sample_scraped_content):
        """Test that generate_questions uses default config parameters."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, 'generate_questions_async') as mock_async:
                mock_async.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = engine.generate_questions(sample_jd, sample_scraped_content)
                
                # Should call async method with no kwargs (using defaults)
                mock_async.assert_called_once_with(sample_jd, sample_scraped_content)
                assert questions == [{"question": "Test", "answer": "Test"}]
    
    def test_generate_questions_with_custom_temperature(self, config, sample_jd, sample_scraped_content):
        """Test that generate_questions accepts custom temperature."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, 'generate_questions_async') as mock_async:
                mock_async.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = engine.generate_questions(
                    sample_jd, 
                    sample_scraped_content, 
                    temperature=0.0
                )
                
                # Should call async method with temperature override
                mock_async.assert_called_once_with(sample_jd, sample_scraped_content, temperature=0.0)
                assert questions == [{"question": "Test", "answer": "Test"}]
    
    def test_generate_questions_with_custom_top_p(self, config, sample_jd, sample_scraped_content):
        """Test that generate_questions accepts custom top_p."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, 'generate_questions_async') as mock_async:
                mock_async.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = engine.generate_questions(
                    sample_jd, 
                    sample_scraped_content, 
                    top_p=0.5
                )
                
                # Should call async method with top_p override
                mock_async.assert_called_once_with(sample_jd, sample_scraped_content, top_p=0.5)
                assert questions == [{"question": "Test", "answer": "Test"}]
    
    def test_generate_questions_with_seed_for_reproducibility(self, config, sample_jd, sample_scraped_content):
        """Test that generate_questions accepts seed for reproducible results."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, 'generate_questions_async') as mock_async:
                mock_async.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = engine.generate_questions(
                    sample_jd, 
                    sample_scraped_content, 
                    temperature=0.0,
                    seed=42
                )
                
                # Should call async method with seed for reproducibility
                mock_async.assert_called_once_with(
                    sample_jd, 
                    sample_scraped_content, 
                    temperature=0.0,
                    seed=42
                )
                assert questions == [{"question": "Test", "answer": "Test"}]
    
    def test_generate_questions_with_multiple_overrides(self, config, sample_jd, sample_scraped_content):
        """Test that generate_questions accepts multiple parameter overrides."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, 'generate_questions_async') as mock_async:
                mock_async.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = engine.generate_questions(
                    sample_jd, 
                    sample_scraped_content, 
                    temperature=0.0,
                    top_p=0.5,
                    max_tokens=1000,
                    seed=42
                )
                
                # Should call async method with all overrides
                mock_async.assert_called_once_with(
                    sample_jd, 
                    sample_scraped_content, 
                    temperature=0.0,
                    top_p=0.5,
                    max_tokens=1000,
                    seed=42
                )
                assert questions == [{"question": "Test", "answer": "Test"}]
    
    @pytest.mark.asyncio
    async def test_generate_questions_async_uses_config_defaults(self, config, sample_jd, sample_scraped_content):
        """Test that generate_questions_async uses config defaults when no overrides provided."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_generate_difficulty_questions_async') as mock_generate:
                mock_generate.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = await engine.generate_questions_async(sample_jd, sample_scraped_content)
                
                # Should call difficulty generator with config defaults
                assert mock_generate.call_count == 3  # easy, medium, hard
                for call in mock_generate.call_args_list:
                    # Check that kwargs are empty (using defaults)
                    args, kwargs = call
                    assert len(args) == 3  # jd, context, difficulty
                    assert len(kwargs) == 0  # No overrides
    
    @pytest.mark.asyncio
    async def test_generate_questions_async_passes_overrides(self, config, sample_jd, sample_scraped_content):
        """Test that generate_questions_async passes overrides to difficulty generators."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_generate_difficulty_questions_async') as mock_generate:
                mock_generate.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                questions = await engine.generate_questions_async(
                    sample_jd, 
                    sample_scraped_content,
                    temperature=0.0,
                    seed=42
                )
                
                # Should call difficulty generator with overrides
                assert mock_generate.call_count == 3  # easy, medium, hard
                for call in mock_generate.call_args_list:
                    # Check that kwargs contain the overrides
                    args, kwargs = call
                    assert kwargs == {'temperature': 0.0, 'seed': 42}
    
    @pytest.mark.asyncio
    async def test_generate_difficulty_questions_async_uses_overrides(self, config, sample_jd):
        """Test that _generate_difficulty_questions_async uses parameter overrides."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                # Mock the streaming response
                mock_stream = AsyncMock()
                mock_create.return_value = mock_stream
                
                # Mock the streaming response processing
                with patch.object(PromptEngine, '_process_streaming_response') as mock_process:
                    mock_process.return_value = {
                        'questions': [
                            {
                                'question': 'Test question?',
                                'answer': 'Test answer.',
                                'category': 'Technical',
                                'skills': ['Python']
                            }
                        ]
                    }
                    
                    engine = PromptEngine(config)
                    questions = await engine._generate_difficulty_questions_async(
                        sample_jd,
                        "Test context",
                        "easy",
                        temperature=0.0,
                        top_p=0.5,
                        seed=42
                    )
                    
                    # Should call OpenAI with overridden parameters
                    mock_create.assert_called_once()
                    call_args = mock_create.call_args[1]
                    
                    assert call_args['temperature'] == 0.0
                    assert call_args['top_p'] == 0.5
                    assert call_args['seed'] == 42
                    assert call_args['max_tokens'] == config.MAX_TOKENS  # Should use default
                    
                    assert len(questions) == 1
                    assert questions[0]['question'] == 'Test question?'
    
    def test_config_defaults_are_sensible(self):
        """Test that config defaults are sensible for reproducible results."""
        config = Config()
        
        # Temperature should be low for consistency
        assert config.TEMPERATURE == 0.3
        assert 0.0 <= config.TEMPERATURE <= 1.0
        
        # Top_p should be reasonable
        assert config.TOP_P == 0.9
        assert 0.0 <= config.TOP_P <= 1.0
        
        # Max tokens should be reasonable
        assert config.MAX_TOKENS == 2000
        assert config.MAX_TOKENS > 0
    
    def test_ci_test_parameters(self, config, sample_jd, sample_scraped_content):
        """Test parameters suitable for CI tests (reproducible results)."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, 'generate_questions_async') as mock_async:
                mock_async.return_value = [{"question": "Test", "answer": "Test"}]
                
                engine = PromptEngine(config)
                
                # CI test parameters for reproducible results
                questions = engine.generate_questions(
                    sample_jd, 
                    sample_scraped_content, 
                    temperature=0.0,  # Deterministic
                    seed=42,         # Fixed seed
                    max_tokens=1000  # Reasonable limit
                )
                
                # Should call async method with CI parameters
                mock_async.assert_called_once_with(
                    sample_jd, 
                    sample_scraped_content, 
                    temperature=0.0,
                    seed=42,
                    max_tokens=1000
                )
                assert questions == [{"question": "Test", "answer": "Test"}]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 