#!/usr/bin/env python3
"""
Tests for utility components.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import json
from typing import Dict, Any, List

# Add the parent directory to the path to import jd_agent
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jd_agent.utils.config import Config
from jd_agent.utils.database import Database
from jd_agent.utils.logger import get_logger
from jd_agent.utils.schemas import QA, QAList
from jd_agent.utils.context import ContextCompressor
from jd_agent.utils.embeddings import EmbeddingManager
from jd_agent.utils.retry import with_openai_backoff
from jd_agent.utils.decorators import timing_decorator
from jd_agent.utils.constants import SYSTEM_PROMPT, DIFFICULTY_DESC


class TestConfig(unittest.TestCase):
    """Test cases for Config utility."""
    
    def test_config_init(self):
        """Test Config initialization."""
        config = Config()
        
        self.assertIsNotNone(config)
        self.assertIsInstance(config.OPENAI_API_KEY, str)
        self.assertIsInstance(config.MAX_TOKENS, int)
        self.assertIsInstance(config.SERPAPI_API_KEY, str)
    
    def test_config_from_env(self):
        """Test Config loading from environment variables."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_openai_key',
            'SERPAPI_API_KEY': 'test_serpapi_key',
            'MAX_TOKENS': '4000'
        }):
            config = Config()
            
            self.assertEqual(config.OPENAI_API_KEY, 'test_openai_key')
            self.assertEqual(config.SERPAPI_API_KEY, 'test_serpapi_key')
            self.assertEqual(config.MAX_TOKENS, 4000)


class TestDatabase(unittest.TestCase):
    """Test cases for Database utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = Database(":memory:")  # Use in-memory database for testing
    
    def test_init(self):
        """Test Database initialization."""
        self.assertIsNotNone(self.db)
    
    def test_create_tables(self):
        """Test table creation."""
        # Tables should be created automatically
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('cached_content', tables)
        self.assertIn('usage_stats', tables)
    
    def test_cache_content(self):
        """Test content caching."""
        url = "https://example.com"
        content = "Test content"
        source = "example.com"
        relevance_score = 0.8
        
        self.db.cache_content(url, content, source, relevance_score)
        
        # Verify content was cached
        cached = self.db.get_cached_content(url)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['url'], url)
        self.assertEqual(cached['content'], content)
    
    def test_get_cached_content(self):
        """Test retrieving cached content."""
        url = "https://example.com"
        content = "Test content"
        
        self.db.cache_content(url, content, "example.com", 0.8)
        cached = self.db.get_cached_content(url)
        
        self.assertIsNotNone(cached)
        self.assertEqual(cached['url'], url)
    
    def test_get_cached_content_not_found(self):
        """Test retrieving non-existent cached content."""
        cached = self.db.get_cached_content("https://nonexistent.com")
        self.assertIsNone(cached)
    
    def test_update_usage_stats(self):
        """Test usage statistics update."""
        self.db.update_usage_stats('serpapi_searches', 1)
        self.db.update_usage_stats('serpapi_cost', 0.1)
        
        stats = self.db.get_usage_stats()
        
        self.assertIn('serpapi_searches', stats)
        self.assertIn('serpapi_cost', stats)
        self.assertEqual(stats['serpapi_searches'], 1)
        self.assertEqual(stats['serpapi_cost'], 0.1)


class TestLogger(unittest.TestCase):
    """Test cases for Logger utility."""
    
    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger(__name__)
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, __name__)
    
    def test_logger_levels(self):
        """Test logger levels."""
        logger = get_logger("test_logger")
        
        # Test that logger can handle different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # No exceptions should be raised
        self.assertTrue(True)


class TestSchemas(unittest.TestCase):
    """Test cases for Schema utilities."""
    
    def test_qa_dataclass(self):
        """Test QA dataclass."""
        qa = QA(
            question="What is Python?",
            answer="Python is a programming language.",
            difficulty="easy",
            category="programming"
        )
        
        self.assertEqual(qa.question, "What is Python?")
        self.assertEqual(qa.answer, "Python is a programming language.")
        self.assertEqual(qa.difficulty, "easy")
        self.assertEqual(qa.category, "programming")
    
    def test_qa_list_dataclass(self):
        """Test QAList dataclass."""
        qa1 = QA(question="Q1", answer="A1", difficulty="easy", category="test")
        qa2 = QA(question="Q2", answer="A2", difficulty="medium", category="test")
        
        qa_list = QAList(questions=[qa1, qa2])
        
        self.assertEqual(len(qa_list.questions), 2)
        self.assertEqual(qa_list.questions[0].question, "Q1")
        self.assertEqual(qa_list.questions[1].question, "Q2")


class TestContextCompressor(unittest.TestCase):
    """Test cases for ContextCompressor utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compressor = ContextCompressor(
            max_tokens=1000,
            char_limit_per_piece=350,
            min_relevance_threshold=0.3
        )
    
    def test_init(self):
        """Test ContextCompressor initialization."""
        self.assertIsNotNone(self.compressor)
        self.assertEqual(self.compressor.max_tokens, 1000)
        self.assertEqual(self.compressor.char_limit_per_piece, 350)
        self.assertEqual(self.compressor.min_relevance_threshold, 0.3)
    
    def test_compress_simple_text(self):
        """Test compression of simple text."""
        text = "This is a simple test text that should be compressed."
        compressed = self.compressor.compress(text)
        
        self.assertIsInstance(compressed, str)
        self.assertLessEqual(len(compressed), len(text))
    
    def test_compress_large_text(self):
        """Test compression of large text."""
        large_text = "This is a very large text. " * 1000
        compressed = self.compressor.compress(large_text)
        
        self.assertIsInstance(compressed, str)
        self.assertLess(len(compressed), len(large_text))
    
    def test_compress_empty_text(self):
        """Test compression of empty text."""
        compressed = self.compressor.compress("")
        
        self.assertEqual(compressed, "")
    
    def test_compress_with_relevance(self):
        """Test compression with relevance scoring."""
        text = "This is a test text with some content."
        compressed = self.compressor.compress(text)
        
        self.assertIsInstance(compressed, str)
        self.assertGreater(len(compressed), 0)


class TestEmbeddingManager(unittest.TestCase):
    """Test cases for EmbeddingManager utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.embedding_manager = EmbeddingManager()
    
    def test_init(self):
        """Test EmbeddingManager initialization."""
        self.assertIsNotNone(self.embedding_manager)
    
    def test_get_embedding(self):
        """Test embedding generation."""
        text = "This is a test text."
        embedding = self.embedding_manager.get_embedding(text)
        
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        text1 = "Python programming language"
        text2 = "Python coding"
        text3 = "JavaScript programming"
        
        embedding1 = self.embedding_manager.get_embedding(text1)
        embedding2 = self.embedding_manager.get_embedding(text2)
        embedding3 = self.embedding_manager.get_embedding(text3)
        
        similarity_12 = self.embedding_manager.calculate_similarity(embedding1, embedding2)
        similarity_13 = self.embedding_manager.calculate_similarity(embedding1, embedding3)
        
        self.assertIsInstance(similarity_12, float)
        self.assertIsInstance(similarity_13, float)
        self.assertGreaterEqual(similarity_12, 0.0)
        self.assertLessEqual(similarity_12, 1.0)
        # Python and Python should be more similar than Python and JavaScript
        self.assertGreater(similarity_12, similarity_13)


class TestRetry(unittest.TestCase):
    """Test cases for retry utility."""
    
    def test_with_openai_backoff_success(self):
        """Test retry decorator with successful call."""
        call_count = 0
        
        @with_openai_backoff
        def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)
    
    def test_with_openai_backoff_failure_then_success(self):
        """Test retry decorator with failure then success."""
        call_count = 0
        
        @with_openai_backoff
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = test_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)


class TestDecorators(unittest.TestCase):
    """Test cases for decorators utility."""
    
    def test_timing_decorator(self):
        """Test timing decorator."""
        @timing_decorator
        def test_function():
            import time
            time.sleep(0.1)
            return "done"
        
        result = test_function()
        
        self.assertEqual(result, "done")


class TestConstants(unittest.TestCase):
    """Test cases for constants utility."""
    
    def test_system_prompt(self):
        """Test system prompt constant."""
        self.assertIsInstance(SYSTEM_PROMPT, str)
        self.assertGreater(len(SYSTEM_PROMPT), 0)
    
    def test_difficulty_desc(self):
        """Test difficulty descriptions constant."""
        self.assertIsInstance(DIFFICULTY_DESC, dict)
        self.assertIn('easy', DIFFICULTY_DESC)
        self.assertIn('medium', DIFFICULTY_DESC)
        self.assertIn('hard', DIFFICULTY_DESC)


if __name__ == '__main__':
    unittest.main() 