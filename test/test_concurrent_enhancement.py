"""
Test the concurrent enhancement functionality in PromptEngine.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from jd_agent.components.prompt_engine import PromptEngine
from jd_agent.utils.config import Config


class TestConcurrentEnhancement:
    """Test concurrent enhancement functionality."""
    
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
    def sample_questions(self):
        return [
            {
                'question': 'What is Python?',
                'answer': 'Python is a programming language',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'question': 'Explain machine learning',
                'answer': 'Machine learning is a subset of AI',
                'category': 'Technical',
                'skills': ['Machine Learning']
            },
            {
                'question': 'What is SQL?',
                'answer': 'SQL is a database language',
                'category': 'Technical',
                'skills': ['SQL']
            },
            {
                'question': 'How does recursion work?',
                'answer': 'Recursion is when a function calls itself',
                'category': 'Technical',
                'skills': ['Algorithms']
            },
            {
                'question': 'What is Docker?',
                'answer': 'Docker is a containerization platform',
                'category': 'Technical',
                'skills': ['Docker']
            }
        ]
    
    @pytest.fixture
    def sample_scraped_content(self):
        return [
            {
                'source': 'GitHub',
                'title': 'Python Programming Guide',
                'content': 'Python is a high-level programming language known for its simplicity and readability.',
                'relevance_score': 0.9
            },
            {
                'source': 'Medium',
                'title': 'Machine Learning Basics',
                'content': 'Machine learning is a subset of artificial intelligence that focuses on building systems.',
                'relevance_score': 0.8
            },
            {
                'source': 'LeetCode',
                'title': 'SQL Interview Questions',
                'content': 'SQL is a standard language for storing, manipulating, and retrieving data.',
                'relevance_score': 0.7
            }
        ]
    
    @pytest.mark.asyncio
    async def test_concurrent_enhancement_basic(self, config, sample_questions, sample_scraped_content):
        """Test basic concurrent enhancement functionality."""
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
                enhanced_questions = await engine.enhance_questions_with_context_async(
                    sample_questions, 
                    sample_scraped_content
                )
                
                # Should have enhanced questions
                assert len(enhanced_questions) == len(sample_questions)
                
                # Check that some questions were enhanced
                enhanced_count = sum(1 for q in enhanced_questions if q.get('enhanced', False))
                assert enhanced_count > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_enhancement_rate_limiting(self, config, sample_questions, sample_scraped_content):
        """Test that rate limiting is enforced with semaphore."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                # Mock responses with delays to test concurrency
                async def delayed_response(*args, **kwargs):
                    await asyncio.sleep(0.1)  # Simulate API delay
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = "Enhanced answer."
                    return mock_response
                
                mock_create.side_effect = delayed_response
                
                engine = PromptEngine(config)
                
                # Time the concurrent enhancement
                start_time = asyncio.get_event_loop().time()
                enhanced_questions = await engine.enhance_questions_with_context_async(
                    sample_questions, 
                    sample_scraped_content
                )
                end_time = asyncio.get_event_loop().time()
                
                # Should have enhanced all questions
                assert len(enhanced_questions) == len(sample_questions)
                
                # With 5 questions and max 5 concurrent requests, should take ~0.1s
                # (all can run concurrently due to semaphore limit)
                elapsed_time = end_time - start_time
                assert elapsed_time < 0.2  # Should be much faster than sequential
    
    @pytest.mark.asyncio
    async def test_concurrent_enhancement_with_exceptions(self, config, sample_questions, sample_scraped_content):
        """Test that exceptions are handled gracefully in concurrent enhancement."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                # Mock some successful and some failed responses
                call_count = 0
                def mock_response(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count % 2 == 0:  # Every other call fails
                        raise Exception("API Error")
                    else:
                        mock_response = Mock()
                        mock_response.choices = [Mock()]
                        mock_response.choices[0].message.content = "Enhanced answer."
                        return mock_response
                
                mock_create.side_effect = mock_response
                
                engine = PromptEngine(config)
                enhanced_questions = await engine.enhance_questions_with_context_async(
                    sample_questions, 
                    sample_scraped_content
                )
                
                # Should still return all questions (some enhanced, some original)
                assert len(enhanced_questions) == len(sample_questions)
                
                # Some should be enhanced, some should be original
                enhanced_count = sum(1 for q in enhanced_questions if q.get('enhanced', False))
                assert enhanced_count > 0
                assert enhanced_count < len(sample_questions)  # Some should fail
    
    @pytest.mark.asyncio
    async def test_concurrent_enhancement_no_client(self, config, sample_questions, sample_scraped_content):
        """Test that enhancement returns original questions when no client available."""
        with patch('openai.OpenAI') as mock_openai:
            mock_openai.return_value = None  # No client
            
            engine = PromptEngine(config)
            enhanced_questions = await engine.enhance_questions_with_context_async(
                sample_questions, 
                sample_scraped_content
            )
            
            # Should return original questions unchanged
            assert enhanced_questions == sample_questions
    
    @pytest.mark.asyncio
    async def test_concurrent_enhancement_no_relevant_content(self, config, sample_questions):
        """Test enhancement when no relevant content is found."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            engine = PromptEngine(config)
            enhanced_questions = await engine.enhance_questions_with_context_async(
                sample_questions, 
                []  # Empty scraped content
            )
            
            # Should return original questions unchanged
            assert enhanced_questions == sample_questions
    
    def test_sync_enhancement_fallback(self, config, sample_questions, sample_scraped_content):
        """Test that sync enhancement falls back to sequential processing."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                # Mock successful responses
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Enhanced answer."
                mock_create.return_value = mock_response
                
                engine = PromptEngine(config)
                enhanced_questions = engine.enhance_questions_with_context(
                    sample_questions, 
                    sample_scraped_content
                )
                
                # Should have enhanced questions
                assert len(enhanced_questions) == len(sample_questions)
                
                # Check that some questions were enhanced
                enhanced_count = sum(1 for q in enhanced_questions if q.get('enhanced', False))
                assert enhanced_count > 0
    
    def test_sync_enhancement_async_error_fallback(self, config, sample_questions, sample_scraped_content):
        """Test that sync enhancement falls back when async fails."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                # Mock successful responses for fallback
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Enhanced answer."
                mock_create.return_value = mock_response
                
                engine = PromptEngine(config)
                
                # Mock asyncio.run to raise an exception
                with patch('asyncio.run') as mock_run:
                    mock_run.side_effect = Exception("Async error")
                    
                    enhanced_questions = engine.enhance_questions_with_context(
                        sample_questions, 
                        sample_scraped_content
                    )
                    
                    # Should still return enhanced questions via fallback
                    assert len(enhanced_questions) == len(sample_questions)
                    enhanced_count = sum(1 for q in enhanced_questions if q.get('enhanced', False))
                    assert enhanced_count > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_enhancement_large_batch(self, config, sample_scraped_content):
        """Test concurrent enhancement with a large batch of questions."""
        # Create a larger batch of questions
        large_questions = []
        for i in range(20):
            large_questions.append({
                'question': f'Question {i}?',
                'answer': f'Answer {i}',
                'category': 'Technical',
                'skills': [f'Skill{i}']
            })
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                # Mock successful responses
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Enhanced answer."
                mock_create.return_value = mock_response
                
                engine = PromptEngine(config)
                
                # Time the concurrent enhancement
                start_time = asyncio.get_event_loop().time()
                enhanced_questions = await engine.enhance_questions_with_context_async(
                    large_questions, 
                    sample_scraped_content
                )
                end_time = asyncio.get_event_loop().time()
                
                # Should have enhanced all questions
                assert len(enhanced_questions) == len(large_questions)
                
                # With 20 questions and max 5 concurrent requests, should be efficient
                elapsed_time = end_time - start_time
                assert elapsed_time < 1.0  # Should be much faster than sequential
    
    @pytest.mark.asyncio
    async def test_concurrent_enhancement_semaphore_behavior(self, config, sample_questions, sample_scraped_content):
        """Test that semaphore properly limits concurrent requests."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Track concurrent executions
            concurrent_count = 0
            max_concurrent = 0
            
            async def track_concurrent(*args, **kwargs):
                nonlocal concurrent_count, max_concurrent
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
                
                # Simulate API delay
                await asyncio.sleep(0.1)
                
                concurrent_count -= 1
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Enhanced answer."
                return mock_response
            
            with patch.object(PromptEngine, '_create_chat_completion_with_retry') as mock_create:
                mock_create.side_effect = track_concurrent
                
                engine = PromptEngine(config)
                enhanced_questions = await engine.enhance_questions_with_context_async(
                    sample_questions, 
                    sample_scraped_content
                )
                
                # Should have enhanced all questions
                assert len(enhanced_questions) == len(sample_questions)
                
                # Should not exceed semaphore limit of 5
                assert max_concurrent <= 5
                assert concurrent_count == 0  # All should complete


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 