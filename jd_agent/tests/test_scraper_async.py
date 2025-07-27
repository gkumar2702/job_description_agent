"""
Unit tests for async web scraper performance and concurrent fetching.
"""

import asyncio
import time
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from ..components.knowledge_miner import FreeWebScraper, ScrapedContent
from ..utils.config import Config


class TestAsyncScraperPerformance:
    """Test async scraper performance and concurrent fetching."""
    
    @pytest.fixture
    def config(self):
        """Create a mock config for testing."""
        config = Mock(spec=Config)
        config.serpapi_key = "test_key"
        return config
    
    @pytest_asyncio.fixture
    async def scraper(self, config):
        """Create an async scraper instance."""
        async with FreeWebScraper(config) as scraper:
            yield scraper
    
    @pytest.mark.asyncio
    async def test_scraper_context_manager(self, config):
        """Test that scraper works as async context manager."""
        async with FreeWebScraper(config) as scraper:
            assert scraper._session is not None
            assert not scraper._session.closed
        
        # Session should be closed after context exit
        assert scraper._session is None
    
    @pytest.mark.asyncio
    async def test_concurrent_fetch_performance(self, scraper):
        """Test that concurrent fetches complete efficiently."""
        # Test URLs that have 1 second delay
        test_urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1"
        ]
        
        start_time = time.time()
        
        # Create tasks for concurrent fetching
        tasks = [scraper.scrape_with_aiohttp(url) for url in test_urls]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate average time per request
        avg_time_per_request = total_time / len(test_urls)
        
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per request: {avg_time_per_request:.2f}s")
        print(f"Results: {len([r for r in results if r is not None])}/{len(results)} successful")
        
        # With throttling (2 requests per second), 5 requests should take at least 2 seconds
        # But concurrent execution should reduce this significantly
        # Allow some flexibility for network delays and throttling
        assert total_time < 5.0, f"Total time ({total_time:.2f}s) is too slow for concurrent requests"
        
        # Verify that at least some requests succeeded
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        assert len(successful_results) > 0, "No requests succeeded"
    
    @pytest.mark.asyncio
    async def test_concurrent_fetch_without_throttling(self, config):
        """Test concurrent fetching without throttling for maximum performance."""
        # Create a scraper without throttling
        async with FreeWebScraper(config) as scraper:
            # Disable throttling for this test
            scraper.throttler = None
            
            # Test URLs that have 1 second delay
            test_urls = [
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1"
            ]
            
            start_time = time.time()
            
            # Create tasks for concurrent fetching
            tasks = [scraper.scrape_with_aiohttp(url) for url in test_urls]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calculate average time per request
            avg_time_per_request = total_time / len(test_urls)
            
            print(f"Total time (no throttling): {total_time:.2f}s")
            print(f"Average time per request: {avg_time_per_request:.2f}s")
            print(f"Results: {len([r for r in results if r is not None])}/{len(results)} successful")
            
            # Without throttling, all requests should complete in roughly 1 second
            # Allow some flexibility for network delays
            assert total_time < 3.0, f"Total time ({total_time:.2f}s) is too slow for concurrent requests without throttling"
            
            # Verify that at least some requests succeeded
            successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
            assert len(successful_results) > 0, "No requests succeeded"
    
    @pytest.mark.asyncio
    async def test_throttling_behavior(self, scraper):
        """Test that throttling works correctly."""
        # Test with multiple rapid requests
        test_urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/get",
            "https://httpbin.org/get",
            "https://httpbin.org/get",
            "https://httpbin.org/get"
        ]
        
        start_time = time.time()
        
        # Make requests sequentially to test throttling
        results = []
        for url in test_urls:
            result = await scraper.scrape_with_aiohttp(url)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # With throttling (2 requests per second), 5 requests should take at least 2 seconds
        # Allow some flexibility for network delays
        assert total_time >= 1.5, f"Throttling not working: {total_time:.2f}s for 5 requests"
        
        # Verify results
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) > 0, "No requests succeeded"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, scraper):
        """Test error handling for invalid URLs."""
        invalid_urls = [
            "https://invalid-domain-that-does-not-exist-12345.com",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500",
        ]
        
        results = []
        for url in invalid_urls:
            result = await scraper.scrape_with_aiohttp(url)
            results.append(result)
        
        # All should return None due to errors
        assert all(r is None for r in results), "Some invalid URLs returned results"
    
    @pytest.mark.asyncio
    async def test_content_extraction(self, scraper):
        """Test that content is properly extracted from valid pages."""
        # Test with a simple HTML page
        test_url = "https://httpbin.org/html"
        
        result = await scraper.scrape_with_aiohttp(test_url)
        
        assert result is not None, "Failed to scrape test URL"
        assert isinstance(result, ScrapedContent), "Result is not ScrapedContent"
        assert result.url == test_url, "URL not preserved"
        assert result.title is not None, "Title not extracted"
        assert result.content is not None, "Content not extracted"
        assert len(result.content) > 0, "Content is empty"
        assert result.source == "httpbin.org", "Source not correctly extracted"
        assert result.relevance_score == 0.0, "Relevance score should be 0.0 initially"
        assert result.timestamp > 0, "Timestamp not set"
    
    @pytest.mark.asyncio
    async def test_session_reuse(self, config):
        """Test that session is properly reused across requests."""
        async with FreeWebScraper(config) as scraper:
            # Make multiple requests
            urls = [
                "https://httpbin.org/get",
                "https://httpbin.org/get",
                "https://httpbin.org/get"
            ]
            
            results = []
            for url in urls:
                result = await scraper.scrape_with_aiohttp(url)
                results.append(result)
            
            # All requests should succeed
            successful_results = [r for r in results if r is not None]
            assert len(successful_results) == len(urls), "Not all requests succeeded"
            
            # Session should still be open
            assert not scraper._session.closed, "Session was closed prematurely"
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, config):
        """Test that connection pool limits are respected."""
        async with FreeWebScraper(config) as scraper:
            # Make many concurrent requests to test connection pool
            urls = [f"https://httpbin.org/get?i={i}" for i in range(20)]
            
            start_time = time.time()
            
            # Create tasks for concurrent fetching
            tasks = [scraper.scrape_with_aiohttp(url) for url in urls]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete within reasonable time (not too slow due to connection limits)
            assert total_time < 10.0, f"Too slow: {total_time:.2f}s for 20 requests"
            
            # Most requests should succeed
            successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
            success_rate = len(successful_results) / len(urls)
            assert success_rate > 0.8, f"Success rate too low: {success_rate:.2%}"
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, scraper):
        """Test that timeouts are handled correctly."""
        # Test with a URL that takes too long
        slow_url = "https://httpbin.org/delay/15"  # 15 second delay
        
        start_time = time.time()
        result = await scraper.scrape_with_aiohttp(slow_url)
        end_time = time.time()
        
        # Should timeout within 15 seconds (with some buffer)
        assert end_time - start_time < 15.0, "Request did not timeout"
        assert result is None, "Slow request should return None"
    
    @pytest.mark.asyncio
    async def test_user_agent_header(self, scraper):
        """Test that User-Agent header is properly set."""
        test_url = "https://httpbin.org/headers"
        
        result = await scraper.scrape_with_aiohttp(test_url)
        
        assert result is not None, "Failed to get headers"
        
        # The response should contain our User-Agent
        expected_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        assert expected_ua in result.content, "User-Agent header not found in response"


class TestScraperIntegration:
    """Integration tests for scraper with real websites."""
    
    @pytest.fixture
    def config(self):
        """Create a mock config for testing."""
        config = Mock(spec=Config)
        config.serpapi_key = "test_key"
        return config
    
    @pytest.mark.asyncio
    async def test_github_api_scraping(self, config):
        """Test scraping GitHub API responses."""
        async with FreeWebScraper(config) as scraper:
            # Test GitHub API endpoint
            url = "https://api.github.com/zen"
            
            result = await scraper.scrape_with_aiohttp(url)
            
            # GitHub API should return JSON, which will be parsed as text
            assert result is not None, "Failed to scrape GitHub API"
            assert result.content is not None, "No content extracted"
            assert len(result.content) > 0, "Content is empty"
    
    @pytest.mark.asyncio
    async def test_html_parsing(self, config):
        """Test that HTML is properly parsed and cleaned."""
        async with FreeWebScraper(config) as scraper:
            # Test with a simple HTML page
            url = "https://httpbin.org/html"
            
            result = await scraper.scrape_with_aiohttp(url)
            
            assert result is not None, "Failed to scrape HTML"
            assert result.title is not None, "Title not extracted"
            assert result.content is not None, "Content not extracted"
            
            # Content should be cleaned (no HTML tags)
            assert "<" not in result.content, "HTML tags not removed"
            assert ">" not in result.content, "HTML tags not removed"
            
            # Content should be truncated to 5000 characters
            assert len(result.content) <= 5000, "Content not truncated"


if __name__ == "__main__":
    # Run performance test directly
    async def main():
        config = Mock(spec=Config)
        config.serpapi_key = "test_key"
        
        async with FreeWebScraper(config) as scraper:
            print("Testing concurrent fetch performance...")
            
            test_urls = [
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1",
                "https://httpbin.org/delay/1"
            ]
            
            start_time = time.time()
            tasks = [scraper.scrape_with_aiohttp(url) for url in test_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            total_time = end_time - start_time
            avg_time = total_time / len(test_urls)
            
            print(f"Total time: {total_time:.2f}s")
            print(f"Average time per request: {avg_time:.2f}s")
            print(f"Success rate: {len([r for r in results if r is not None])}/{len(results)}")
            
            if avg_time <= 0.2:
                print("✅ Performance test PASSED")
            else:
                print("❌ Performance test FAILED")
    
    asyncio.run(main()) 