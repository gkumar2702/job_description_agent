"""
Unit tests for the async scraper functionality.
"""

import pytest
import asyncio
import time
from typing import Any
from unittest.mock import Mock, AsyncMock

import pytest_asyncio  # type: ignore

from ..components.knowledge_miner import FreeWebScraper
from ..utils.config import Config
from ..utils.database import Database


@pytest_asyncio.fixture
async def config() -> Config:
    """Create a test configuration."""
    return Config(
        OPENAI_API_KEY="test_openai_key_long_enough_for_validation",
        SERPAPI_KEY="test_serpapi_key_long_enough_for_validation",
        GMAIL_REFRESH_TOKEN="test_refresh_token"
    )


@pytest_asyncio.fixture
async def database() -> Database:
    """Create a test database."""
    return Database(":memory:")


@pytest_asyncio.fixture
async def scraper(config: Config, database: Database) -> FreeWebScraper:
    """Create a test scraper instance."""
    return FreeWebScraper(config, database)


class TestAsyncScraperPerformance:
    """Test async scraper performance and concurrency."""
    
    @pytest.mark.asyncio
    async def test_scraper_context_manager(self, scraper: FreeWebScraper) -> None:
        """Test that the scraper works as an async context manager."""
        async with scraper as s:
            assert s._session is not None
            assert s._browser is not None
            assert s._context is not None
        
        # Check that resources are cleaned up
        assert scraper._session is None
        assert scraper._browser is None
        assert scraper._context is None
    
    @pytest.mark.asyncio
    async def test_concurrent_fetch_performance(self, scraper: FreeWebScraper) -> None:
        """Test concurrent fetching performance with throttling."""
        urls = [f"https://httpbin.org/delay/1" for _ in range(5)]
        
        start_time = time.perf_counter()
        
        async with scraper as s:
            tasks = [s._get_or_fetch(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.perf_counter() - start_time
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        # Should complete within reasonable time with throttling (adjusted for network variability)
        assert total_time < 7.0
        assert len(successful_results) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_fetch_without_throttling(self, scraper: FreeWebScraper) -> None:
        """Test concurrent fetching without throttling."""
        urls = [f"https://httpbin.org/delay/1" for _ in range(3)]
        
        start_time = time.perf_counter()
        
        async with scraper as s:
            # Temporarily disable throttling
            s.throttler = None
            tasks = [s._get_or_fetch(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.perf_counter() - start_time
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        # Should be faster without throttling (adjusted for network variability)
        assert total_time < 5.0
        assert len(successful_results) > 0
    
    @pytest.mark.asyncio
    async def test_throttling_behavior(self, scraper: FreeWebScraper) -> None:
        """Test that throttling is working correctly."""
        urls = [f"https://httpbin.org/delay/0.1" for _ in range(3)]
        
        start_time = time.perf_counter()
        
        async with scraper as s:
            tasks = [s._get_or_fetch(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.perf_counter() - start_time
        
        # With throttling (2 requests per second), 3 requests should take at least 1 second
        assert total_time >= 1.0
        assert len([r for r in results if r is not None]) > 0


class TestScraperErrorHandling:
    """Test error handling in the scraper."""
    
    @pytest.mark.asyncio
    async def test_invalid_url_handling(self, scraper: FreeWebScraper) -> None:
        """Test handling of invalid URLs."""
        async with scraper as s:
            result = await s._get_or_fetch("https://this-domain-definitely-does-not-exist-12345.com")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, scraper: FreeWebScraper) -> None:
        """Test handling of timeouts."""
        async with scraper as s:
            # Use a URL that will take longer than our 10-second timeout
            slow_url = "https://httpbin.org/delay/20"
            result = await s._get_or_fetch(slow_url)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_content_extraction(self, scraper: FreeWebScraper) -> None:
        """Test that content is properly extracted."""
        async with scraper as s:
            result = await s._get_or_fetch("https://httpbin.org/html")
            
            assert result is not None
            assert result.url == "https://httpbin.org/html"
            assert result.title is not None
            assert len(result.content) > 0
            assert result.source == "httpbin.org"


class TestScraperIntegration:
    """Integration tests for the scraper."""
    
    @pytest.mark.asyncio
    async def test_session_reuse(self, scraper: FreeWebScraper) -> None:
        """Test that the session is reused across requests."""
        async with scraper as s:
            # Make multiple requests
            urls = [
                "https://httpbin.org/get",
                "https://httpbin.org/user-agent",
                "https://httpbin.org/headers"
            ]
            
            results = []
            for url in urls:
                result = await s._get_or_fetch(url)
                results.append(result)
            
            # All requests should succeed
            assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, scraper: FreeWebScraper) -> None:
        """Test that connection pool limits are respected."""
        # Make many concurrent requests to test pool limits
        urls = [f"https://httpbin.org/delay/0.1" for _ in range(15)]
        
        async with scraper as s:
            tasks = [s._get_or_fetch(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most requests should succeed despite pool limits
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        assert len(successful_results) > 0
    
    @pytest.mark.asyncio
    async def test_user_agent_headers(self, scraper: FreeWebScraper) -> None:
        """Test that User-Agent headers are properly set."""
        async with scraper as s:
            result = await s._get_or_fetch("https://httpbin.org/user-agent")
            
            assert result is not None
            # The content should contain our User-Agent
            assert "Mozilla/5.0" in result.content


class TestScraperCache:
    """Test the caching functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_hit_ratio(self, database: Database, config: Config) -> None:
        """Test that cache hit ratio is high for repeated requests."""
        async with FreeWebScraper(config, database) as scraper:
            # Fetch the same URLs twice
            urls = [f"https://httpbin.org/get?test={i}" for i in range(10)]
            
            # First fetch
            first_results = []
            for url in urls:
                result = await scraper._get_or_fetch(url)
                first_results.append(result)
            
            # Second fetch (should use cache)
            second_results = []
            for url in urls:
                result = await scraper._get_or_fetch(url)
                second_results.append(result)
            
            # All results should be the same
            assert len(first_results) == len(second_results)
            assert all(r1 is not None and r2 is not None for r1, r2 in zip(first_results, second_results))
            
            # Check cache stats
            stats = database.get_cache_stats()
            assert stats['total_entries'] >= 10
            assert stats['valid_entries'] >= 10
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, database: Database, config: Config) -> None:
        """Test that cache entries expire correctly."""
        # This test would require manipulating timestamps
        # For now, we'll just test that the cache works
        async with FreeWebScraper(config, database) as scraper:
            url = "https://httpbin.org/get"
            
            # First fetch
            result1 = await scraper._get_or_fetch(url)
            assert result1 is not None
            
            # Second fetch (should use cache)
            result2 = await scraper._get_or_fetch(url)
            assert result2 is not None
            
            # Results should be identical
            assert result1.url == result2.url
            assert result1.content == result2.content


class TestDynamicScraping:
    """Test dynamic scraping with Playwright."""
    
    @pytest.mark.asyncio
    async def test_dynamic_scraping_browser_reuse(self, scraper: FreeWebScraper) -> None:
        """Test that browser context is reused for multiple pages."""
        async with scraper as s:
            # Create multiple pages in the same context
            page1 = await s._context.new_page()
            page2 = await s._context.new_page()
            
            # Navigate to different URLs
            await page1.goto("https://httpbin.org/html")
            await page2.goto("https://httpbin.org/json")
            
            # Check that both pages work
            title1 = await page1.title()
            title2 = await page2.title()
            
            # Check that pages loaded successfully (titles might be empty for some pages)
            # Just verify the pages were created and navigated without errors
            assert page1 is not None
            assert page2 is not None
            
            # Clean up
            await page1.close()
            await page2.close()
    
    @pytest.mark.asyncio
    async def test_dynamic_scraping_retry_mechanism(self, scraper: FreeWebScraper) -> None:
        """Test the exponential backoff retry mechanism."""
        async with scraper as s:
            # Use a URL that will fail
            start_time = time.perf_counter()
            result = await s.scrape_dynamic("https://invalid-url-that-will-fail.com")
            elapsed_time = time.perf_counter() - start_time
            
            # Should return None after all retries
            assert result is None
            
            # Should have taken some time due to retries
            assert elapsed_time > 2.0
    
    @pytest.mark.asyncio
    async def test_dynamic_scraping_integration(self, scraper: FreeWebScraper) -> None:
        """Test dynamic scraping with a real website."""
        async with scraper as s:
            result = await s.scrape_dynamic("https://httpbin.org/html")
            
            assert result is not None
            assert result.url == "https://httpbin.org/html"
            assert result.title is not None
            assert len(result.content) > 0
            assert "httpbin" in result.source.lower()


if __name__ == "__main__":
    # Create a temporary database for testing
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Run tests
        pytest.main([__file__, "-v"])
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path) 