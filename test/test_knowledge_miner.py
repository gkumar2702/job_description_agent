#!/usr/bin/env python3
"""
Tests for KnowledgeMiner component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
import os
from typing import Dict, Any, List

# Add the parent directory to the path to import jd_agent
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jd_agent.components.knowledge_miner import KnowledgeMiner, FreeWebScraper, ScrapedContent
from jd_agent.components.jd_parser import JobDescription
from jd_agent.utils.config import Config
from jd_agent.utils.database import Database


class TestKnowledgeMiner(unittest.TestCase):
    """Test cases for KnowledgeMiner component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        self.database = Mock(spec=Database)
        
        self.miner = KnowledgeMiner(self.config, self.database)
        
        # Sample job description
        self.sample_jd = JobDescription(
            company="TechCorp",
            role="Senior Software Engineer",
            location="San Francisco, CA",
            experience_years=5,
            skills=["Python", "JavaScript", "React", "AWS"],
            content="We are looking for a Senior Software Engineer...",
            email_id="test_email_id"
        )
        
        # Sample scraped content
        self.sample_scraped_content = ScrapedContent(
            url="https://example.com/interview-questions",
            title="Python Interview Questions",
            content="This article contains common Python interview questions...",
            source="example.com",
            relevance_score=0.8,
            timestamp=1234567890.0
        )
    
    def test_init(self):
        """Test KnowledgeMiner initialization."""
        self.assertIsNotNone(self.miner)
        self.assertEqual(self.miner.config, self.config)
        self.assertEqual(self.miner.database, self.database)
    
    def test_scraped_content_dataclass(self):
        """Test ScrapedContent dataclass."""
        content = ScrapedContent(
            url="https://test.com",
            title="Test Title",
            content="Test content",
            source="test.com",
            relevance_score=0.9,
            timestamp=1234567890.0
        )
        
        self.assertEqual(content.url, "https://test.com")
        self.assertEqual(content.title, "Test Title")
        self.assertEqual(content.content, "Test content")
        self.assertEqual(content.source, "test.com")
        self.assertEqual(content.relevance_score, 0.9)
        self.assertEqual(content.timestamp, 1234567890.0)
    
    def test_build_search_queries(self):
        """Test search query building."""
        queries = self.miner._build_search_queries(self.sample_jd)
        
        self.assertIsInstance(queries, list)
        self.assertGreater(len(queries), 0)
        
        # Check that queries contain relevant terms
        query_text = " ".join(queries).lower()
        self.assertIn("python", query_text)
        self.assertIn("software engineer", query_text)
        self.assertIn("interview", query_text)
    
    def test_calculate_relevance_score(self):
        """Test relevance score calculation."""
        content = ScrapedContent(
            url="https://example.com",
            title="Python Interview Questions for Software Engineers",
            content="This article discusses Python interview questions for software engineers...",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score = self.miner._calculate_relevance_score(content, self.sample_jd)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_filter_and_score_content(self):
        """Test content filtering and scoring."""
        content_list = [
            ScrapedContent(
                url="https://example1.com",
                title="Python Interview Questions",
                content="Python interview questions...",
                source="example1.com",
                relevance_score=0.0,
                timestamp=1234567890.0
            ),
            ScrapedContent(
                url="https://example2.com",
                title="JavaScript Interview Questions",
                content="JavaScript interview questions...",
                source="example2.com",
                relevance_score=0.0,
                timestamp=1234567890.0
            )
        ]
        
        filtered_content = self.miner._filter_and_score_content(content_list, self.sample_jd)
        
        self.assertIsInstance(filtered_content, list)
        self.assertLessEqual(len(filtered_content), len(content_list))
        
        # Check that content has been scored
        for content in filtered_content:
            self.assertGreater(content.relevance_score, 0.0)
    
    def test_get_serpapi_usage(self):
        """Test SerpAPI usage tracking."""
        usage = self.miner.get_serpapi_usage()
        
        self.assertIsInstance(usage, dict)
        self.assertIn('searches', usage)
        self.assertIn('total_cost', usage)
    
    def test_get_cache_stats(self):
        """Test cache statistics."""
        stats = self.miner.get_cache_stats()
        
        self.assertIsInstance(stats, dict)
    
    def test_get_usage_stats(self):
        """Test usage statistics."""
        stats = self.miner.get_usage_stats()
        
        self.assertIsInstance(stats, dict)
    
    @patch('aiohttp.ClientSession')
    @patch('playwright.async_api.async_playwright')
    async def test_free_web_scraper_context_manager(self, mock_playwright, mock_session):
        """Test FreeWebScraper as async context manager."""
        # Mock playwright
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        
        mock_playwright.return_value.start.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        
        # Mock session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        async with FreeWebScraper(self.config, self.database) as scraper:
            self.assertIsNotNone(scraper)
            self.assertEqual(scraper.config, self.config)
            self.assertEqual(scraper.database, self.database)
        
        # Check cleanup
        mock_session_instance.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
    
    @patch('aiohttp.ClientSession.get')
    async def test_scrape_with_aiohttp(self, mock_get):
        """Test aiohttp scraping."""
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text.return_value = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Content</h1>
                <p>This is test content for scraping.</p>
            </body>
        </html>
        """
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Mock database
        self.database.get_cached_content.return_value = None
        
        async with FreeWebScraper(self.config, self.database) as scraper:
            content = await scraper.scrape_with_aiohttp("https://example.com")
            
            self.assertIsNotNone(content)
            self.assertEqual(content.url, "https://example.com")
            self.assertEqual(content.title, "Test Page")
            self.assertIn("Test Content", content.content)
    
    @patch('aiohttp.ClientSession.get')
    async def test_scrape_with_aiohttp_error(self, mock_get):
        """Test aiohttp scraping with error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Mock database
        self.database.get_cached_content.return_value = None
        
        async with FreeWebScraper(self.config, self.database) as scraper:
            content = await scraper.scrape_with_aiohttp("https://example.com")
            
            self.assertIsNone(content)
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_or_fetch_cached(self, mock_get):
        """Test content fetching with cache hit."""
        # Mock cached content
        cached_data = {
            'content': json.dumps({
                'url': 'https://example.com',
                'title': 'Cached Title',
                'content': 'Cached content',
                'source': 'example.com',
                'relevance_score': 0.8,
                'timestamp': 1234567890.0
            })
        }
        self.database.get_cached_content.return_value = cached_data
        
        async with FreeWebScraper(self.config, self.database) as scraper:
            content = await scraper._get_or_fetch("https://example.com")
            
            self.assertIsNotNone(content)
            self.assertEqual(content.title, "Cached Title")
            self.assertEqual(content.content, "Cached content")
            # Should not call aiohttp
            mock_get.assert_not_called()
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_or_fetch_no_cache(self, mock_get):
        """Test content fetching without cache."""
        # Mock no cache
        self.database.get_cached_content.return_value = None
        
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text.return_value = """
        <html>
            <head><title>Test Page</title></head>
            <body><h1>Test Content</h1></body>
        </html>
        """
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with FreeWebScraper(self.config, self.database) as scraper:
            content = await scraper._get_or_fetch("https://example.com")
            
            self.assertIsNotNone(content)
            self.assertEqual(content.title, "Test Page")
            # Should call aiohttp
            mock_get.assert_called_once()
    
    @patch.object(KnowledgeMiner, '_scrape_direct_sources')
    @patch.object(KnowledgeMiner, '_search_with_serpapi')
    @patch.object(KnowledgeMiner, '_free_search_alternatives')
    async def test_mine_knowledge(self, mock_free_search, mock_serpapi, mock_direct):
        """Test knowledge mining process."""
        # Mock responses
        mock_direct.return_value = [self.sample_scraped_content]
        mock_serpapi.return_value = []
        mock_free_search.return_value = []
        
        content_list = await self.miner.mine_knowledge(self.sample_jd)
        
        self.assertIsInstance(content_list, list)
        mock_direct.assert_called_once()
        mock_serpapi.assert_called_once()
        mock_free_search.assert_called_once()
    
    @patch.object(KnowledgeMiner, '_scrape_direct_sources')
    async def test_scrape_direct_sources(self, mock_scrape):
        """Test direct source scraping."""
        mock_scrape.return_value = [self.sample_scraped_content]
        
        async with FreeWebScraper(self.config, self.database) as scraper:
            content_list = await self.miner._scrape_direct_sources(self.sample_jd, scraper)
            
            self.assertIsInstance(content_list, list)
            mock_scrape.assert_called_once()
    
    @patch.object(KnowledgeMiner, '_search_github')
    @patch.object(KnowledgeMiner, '_search_reddit')
    async def test_free_search_alternatives(self, mock_reddit, mock_github):
        """Test free search alternatives."""
        mock_github.return_value = [self.sample_scraped_content]
        mock_reddit.return_value = []
        
        async with FreeWebScraper(self.config, self.database) as scraper:
            content_list = await self.miner._free_search_alternatives(self.sample_jd, scraper)
            
            self.assertIsInstance(content_list, list)
            mock_github.assert_called_once()
            mock_reddit.assert_called_once()


if __name__ == '__main__':
    unittest.main() 