"""
Test the retry decorator functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from openai import RateLimitError, APITimeoutError, APIConnectionError, OpenAIError

from jd_agent.utils.retry import with_backoff, with_openai_backoff, with_gentle_backoff, with_aggressive_backoff


def create_mock_openai_error(error_class, message):
    """Create a mock OpenAI error with proper parameters."""
    if error_class == RateLimitError:
        return RateLimitError(message, response=MagicMock(), body=MagicMock())
    elif error_class == APITimeoutError:
        return APITimeoutError(message)
    elif error_class == APIConnectionError:
        return APIConnectionError(message=message, request=MagicMock())
    else:
        return OpenAIError(message)


class TestRetryDecorator:
    """Test the retry decorator functionality."""
    
    def test_successful_call_no_retry(self):
        """Test that successful calls don't retry."""
        mock_func = Mock(return_value="success")
        
        @with_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_rate_limit_error(self):
        """Test retry on rate limit error."""
        mock_func = Mock()
        mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
        
        @with_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that max retries are respected."""
        mock_func = Mock()
        mock_func.side_effect = create_mock_openai_error(RateLimitError, "Rate limit")
        
        @with_backoff(max_retries=2)
        def test_func():
            return mock_func()
        
        with pytest.raises(RateLimitError):
            test_func()
        
        assert mock_func.call_count == 3  # Initial call + 2 retries
    
    def test_retry_on_multiple_errors(self):
        """Test retry on different types of errors."""
        mock_func = Mock()
        mock_func.side_effect = [
            create_mock_openai_error(RateLimitError, "Rate limit"),
            create_mock_openai_error(APITimeoutError, "Timeout"),
            "success"
        ]
        
        @with_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_non_retryable_error_immediate_failure(self):
        """Test that non-retryable errors fail immediately."""
        mock_func = Mock()
        mock_func.side_effect = ValueError("Not retryable")
        
        @with_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError):
            test_func()
        
        assert mock_func.call_count == 1
    
    def test_custom_retry_exceptions(self):
        """Test custom retry exceptions."""
        mock_func = Mock()
        mock_func.side_effect = [ValueError("Custom error"), "success"]
        
        @with_backoff(max_retries=3, retry_exceptions=(ValueError,))
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_delay_calculation(self):
        """Test delay calculation with exponential backoff."""
        mock_func = Mock()
        mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
        
        with patch('time.sleep') as mock_sleep:
            @with_backoff(max_retries=1, base_delay=1.0, exponential_base=2.0)
            def test_func():
                return mock_func()
            
            test_func()
            
            # Should have slept once with delay ≈ 1.0 * 2^0 = 1.0
            assert mock_sleep.call_count == 1
            call_args = mock_sleep.call_args[0][0]
            assert 0.5 <= call_args <= 1.5  # Allow for jitter
    
    def test_max_delay_respected(self):
        """Test that max delay is respected."""
        mock_func = Mock()
        mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
        
        with patch('time.sleep') as mock_sleep:
            @with_backoff(max_retries=1, base_delay=10.0, max_delay=5.0)
            def test_func():
                return mock_func()
            
            test_func()
            
            # Should have slept once with delay capped at 5.0
            assert mock_sleep.call_count == 1
            call_args = mock_sleep.call_args[0][0]
            assert call_args <= 5.0


class TestAsyncRetryDecorator:
    """Test the async retry decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_async_successful_call_no_retry(self):
        """Test that successful async calls don't retry."""
        mock_func = Mock(return_value="success")
        
        @with_backoff(max_retries=3)
        async def test_func():
            return mock_func()
        
        result = await test_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_retry_on_rate_limit_error(self):
        """Test async retry on rate limit error."""
        mock_func = Mock()
        mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
        
        @with_backoff(max_retries=3)
        async def test_func():
            return mock_func()
        
        result = await test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_max_retries_exceeded(self):
        """Test that async max retries are respected."""
        mock_func = Mock()
        mock_func.side_effect = create_mock_openai_error(RateLimitError, "Rate limit")
        
        @with_backoff(max_retries=2)
        async def test_func():
            return mock_func()
        
        with pytest.raises(RateLimitError):
            await test_func()
        
        assert mock_func.call_count == 3  # Initial call + 2 retries
    
    @pytest.mark.asyncio
    async def test_async_delay_calculation(self):
        """Test async delay calculation with exponential backoff."""
        mock_func = Mock()
        mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
        
        with patch('asyncio.sleep') as mock_sleep:
            @with_backoff(max_retries=1, base_delay=1.0, exponential_base=2.0)
            async def test_func():
                return mock_func()
            
            await test_func()
            
            # Should have slept once with delay ≈ 1.0 * 2^0 = 1.0
            assert mock_sleep.call_count == 1
            call_args = mock_sleep.call_args[0][0]
            assert 0.5 <= call_args <= 1.5  # Allow for jitter


class TestConvenienceDecorators:
    """Test the convenience retry decorators."""
    
    def test_with_openai_backoff(self):
        """Test the OpenAI-specific retry decorator."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"  # Add name attribute
        mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
        
        decorated_func = with_openai_backoff(mock_func)
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_with_gentle_backoff(self):
        """Test the gentle retry decorator."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"  # Add name attribute
        mock_func.side_effect = [create_mock_openai_error(APITimeoutError, "Timeout"), "success"]
        
        decorated_func = with_gentle_backoff(mock_func)
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_with_aggressive_backoff(self):
        """Test the aggressive retry decorator."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"  # Add name attribute
        mock_func.side_effect = [create_mock_openai_error(APIConnectionError, "Connection"), "success"]
        
        decorated_func = with_aggressive_backoff(mock_func)
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 2


class TestRetryIntegration:
    """Test retry integration with real scenarios."""
    
    def test_retry_with_logging(self):
        """Test that retry logs warnings appropriately."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"  # Add name attribute
        mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
        
        with patch('jd_agent.utils.retry.logger') as mock_logger:
            @with_backoff(max_retries=1)
            def test_func():
                return mock_func()
            
            result = test_func()
            
            assert result == "success"
            # Should have logged a warning about the retry
            assert mock_logger.warning.called
    
    def test_retry_with_error_logging(self):
        """Test that retry logs errors when max retries exceeded."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"  # Add name attribute
        mock_func.side_effect = create_mock_openai_error(RateLimitError, "Rate limit")
        
        with patch('jd_agent.utils.retry.logger') as mock_logger:
            @with_backoff(max_retries=1)
            def test_func():
                return mock_func()
            
            with pytest.raises(RateLimitError):
                test_func()
            
            # Should have logged an error about max retries
            assert mock_logger.error.called
    
    def test_jitter_variation(self):
        """Test that jitter adds variation to delays."""
        delays = []
        
        for _ in range(10):
            mock_func = Mock()
            mock_func.side_effect = [create_mock_openai_error(RateLimitError, "Rate limit"), "success"]
            
            with patch('time.sleep') as mock_sleep:
                @with_backoff(max_retries=1, base_delay=1.0, jitter=True)
                def test_func():
                    return mock_func()
                
                test_func()
                delays.append(mock_sleep.call_args[0][0])
        
        # Delays should vary due to jitter
        assert len(set(delays)) > 1
        # All delays should be within reasonable bounds
        for delay in delays:
            assert 0.5 <= delay <= 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 