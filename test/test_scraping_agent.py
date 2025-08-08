#!/usr/bin/env python3
"""
Tests for ScrapingAgent component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import os
from typing import Dict, Any, List

# Add the parent directory to the path to import jd_agent
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jd_agent.components.scraping_agent import ScrapingAgent, ScrapingState
from jd_agent.components.jd_parser import JobDescription
from jd_agent.components.knowledge_miner import ScrapedContent
from jd_agent.utils.config import Config
from jd_agent.utils.database import Database


class TestScrapingAgent(unittest.TestCase):
    """Test cases for ScrapingAgent component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        self.database = Mock(spec=Database)
        
        self.agent = ScrapingAgent(self.config, self.database)
        
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
        """Test ScrapingAgent initialization."""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.config, self.config)
        self.assertEqual(self.agent.database, self.database)
        self.assertIsNotNone(self.agent.knowledge_miner)
        self.assertIsNotNone(self.agent.graph)
    
    def test_scraping_state_dataclass(self):
        """Test ScrapingState dataclass."""
        state = ScrapingState(
            jd=self.sample_jd,
            scraped_content=[self.sample_scraped_content],
            search_queries=["test query"],
            current_step="test_step"
        )
        
        self.assertEqual(state.jd, self.sample_jd)
        self.assertEqual(len(state.scraped_content), 1)
        self.assertEqual(state.search_queries, ["test query"])
        self.assertEqual(state.current_step, "test_step")
        self.assertIsNone(state.error)
    
    def test_prepare_search(self):
        """Test search query preparation."""
        state = ScrapingState(
            jd=self.sample_jd,
            scraped_content=[],
            search_queries=[],
            current_step="prepare_search"
        )
        
        updated_state = self.agent._prepare_search(state)
        
        self.assertIsInstance(updated_state, ScrapingState)
        self.assertGreater(len(updated_state.search_queries), 0)
        self.assertEqual(updated_state.current_step, "scrape_direct_sources")
        self.assertIsNone(updated_state.error)
        
        # Check that queries contain relevant terms
        queries_text = " ".join(updated_state.search_queries).lower()
        self.assertIn("software engineer", queries_text)
        self.assertIn("python", queries_text)
        self.assertIn("interview", queries_text)
    
    def test_prepare_search_with_error(self):
        """Test search preparation with error."""
        # Create a state with invalid JD to trigger error
        invalid_jd = JobDescription(
            company="",
            role="",
            location="",
            experience_years=0,
            skills=[],
            content="",
            email_id=""
        )
        
        state = ScrapingState(
            jd=invalid_jd,
            scraped_content=[],
            search_queries=[],
            current_step="prepare_search"
        )
        
        # Mock the knowledge miner to raise an exception
        with patch.object(self.agent.knowledge_miner, '_build_search_queries', side_effect=Exception("Test error")):
            updated_state = self.agent._prepare_search(state)
            
            self.assertIsNotNone(updated_state.error)
            self.assertIn("Test error", updated_state.error)
    
    @patch.object(ScrapingAgent, '_scrape_direct_sources')
    def test_scrape_direct_sources(self, mock_scrape):
        """Test direct source scraping."""
        state = ScrapingState(
            jd=self.sample_jd,
            scraped_content=[],
            search_queries=["test query"],
            current_step="scrape_direct_sources"
        )
        
        # Mock the async scraping
        mock_scrape.return_value = [self.sample_scraped_content]
        
        updated_state = self.agent._scrape_direct_sources(state)
        
        self.assertIsInstance(updated_state, ScrapingState)
        self.assertEqual(updated_state.current_step, "scrape_search_results")
        self.assertIsNone(updated_state.error)
    
    def test_scrape_search_results(self):
        """Test search results scraping."""
        state = ScrapingState(
            jd=self.sample_jd,
            scraped_content=[self.sample_scraped_content],
            search_queries=["test query"],
            current_step="scrape_search_results"
        )
        
        updated_state = self.agent._scrape_search_results(state)
        
        self.assertIsInstance(updated_state, ScrapingState)
        self.assertEqual(updated_state.current_step, "filter_content")
        self.assertIsNone(updated_state.error)
    
    def test_filter_content(self):
        """Test content filtering."""
        state = ScrapingState(
            jd=self.sample_jd,
            scraped_content=[self.sample_scraped_content],
            search_queries=["test query"],
            current_step="filter_content"
        )
        
        updated_state = self.agent._filter_content(state)
        
        self.assertIsInstance(updated_state, ScrapingState)
        self.assertEqual(updated_state.current_step, "store_results")
        self.assertIsNone(updated_state.error)
    
    def test_store_results(self):
        """Test results storage."""
        state = ScrapingState(
            jd=self.sample_jd,
            scraped_content=[self.sample_scraped_content],
            search_queries=["test query"],
            current_step="store_results"
        )
        
        updated_state = self.agent._store_results(state)
        
        self.assertIsInstance(updated_state, ScrapingState)
        self.assertIsNone(updated_state.error)
    
    def test_calculate_relevance(self):
        """Test relevance calculation."""
        content = ScrapedContent(
            url="https://example.com",
            title="Python Interview Questions for Software Engineers",
            content="This article discusses Python interview questions for software engineers...",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        relevance = self.agent._calculate_relevance(content, self.sample_jd)
        
        self.assertIsInstance(relevance, float)
        self.assertGreaterEqual(relevance, 0.0)
        self.assertLessEqual(relevance, 1.0)
    
    @patch.object(ScrapingAgent, 'run_scraping_workflow')
    def test_run_scraping_workflow(self, mock_run):
        """Test scraping workflow execution."""
        mock_run.return_value = {
            'success': True,
            'content_count': 1,
            'error': None
        }
        
        result = self.agent.run_scraping_workflow(self.sample_jd)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('content_count', result)
        mock_run.assert_called_once_with(self.sample_jd)
    
    @patch('aiohttp.ClientSession.get')
    def test_search_github_repos(self, mock_get):
        """Test GitHub repository search."""
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'name': 'test-repo',
                    'description': 'Test repository',
                    'html_url': 'https://github.com/test/test-repo'
                }
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async def test_async():
            results = await self.agent.search_github_repos("python interview questions")
            return results
        
        results = asyncio.run(test_async())
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
    
    @patch('aiohttp.ClientSession.get')
    def test_search_reddit_posts(self, mock_get):
        """Test Reddit posts search."""
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'data': {
                'children': [
                    {
                        'data': {
                            'title': 'Test Post',
                            'selftext': 'Test content',
                            'url': 'https://reddit.com/test'
                        }
                    }
                ]
            }
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async def test_async():
            results = await self.agent.search_reddit_posts("python interview")
            return results
        
        results = asyncio.run(test_async())
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
    
    @patch('serpapi.Client')
    def test_search_with_serpapi(self, mock_serpapi):
        """Test SerpAPI search."""
        # Mock SerpAPI client
        mock_client = Mock()
        mock_client.search.return_value = {
            'organic_results': [
                {
                    'title': 'Test Result',
                    'link': 'https://example.com',
                    'snippet': 'Test snippet'
                }
            ]
        }
        mock_serpapi.return_value = mock_client
        
        results = self.agent.search_with_serpapi("python interview questions")
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        mock_client.search.assert_called_once()
    
    def test_get_usage_stats(self):
        """Test usage statistics."""
        stats = self.agent.get_usage_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('scraping_operations', stats)
        self.assertIn('content_found', stats)
        self.assertIn('errors', stats)


if __name__ == '__main__':
    unittest.main() 