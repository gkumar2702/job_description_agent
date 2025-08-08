#!/usr/bin/env python3
"""
Tests for PromptEngine component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import os
from typing import Dict, Any, List

# Add the parent directory to the path to import jd_agent
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jd_agent.components.prompt_engine import PromptEngine
from jd_agent.components.jd_parser import JobDescription
from jd_agent.utils.config import Config


class TestPromptEngine(unittest.TestCase):
    """Test cases for PromptEngine component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        self.config.OPENAI_API_KEY = "test_api_key"
        self.config.MAX_TOKENS = 4000
        
        self.engine = PromptEngine(self.config)
        
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
        self.sample_scraped_content = [
            {
                "url": "https://example.com/tech-article",
                "title": "Modern Software Development Practices",
                "content": "This article discusses modern software development practices...",
                "relevance_score": 0.8
            },
            {
                "url": "https://example.com/python-guide",
                "title": "Python Best Practices",
                "content": "A comprehensive guide to Python best practices...",
                "relevance_score": 0.9
            }
        ]
    
    def test_init(self):
        """Test PromptEngine initialization."""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.config, self.config)
        self.assertIsNotNone(self.engine.client)
        self.assertIsNotNone(self.engine.context_compressor)
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        config = Config()
        config.OPENAI_API_KEY = None
        
        engine = PromptEngine(config)
        self.assertIsNone(engine.client)
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        text = "This is a test text with some content."
        tokens = self.engine._estimate_tokens(text)
        
        self.assertIsInstance(tokens, int)
        self.assertGreater(tokens, 0)
        
        # Test with longer text
        long_text = "This is a much longer text that should have more tokens. " * 10
        long_tokens = self.engine._estimate_tokens(long_text)
        self.assertGreater(long_tokens, tokens)
    
    @patch('openai.OpenAI')
    def test_generate_questions_sync(self, mock_openai):
        """Test synchronous question generation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"questions": [{"question": "Test question", "difficulty": "medium"}]}'
        mock_client.chat.completions.create.return_value = mock_response
        
        questions = self.engine.generate_questions(self.sample_jd, self.sample_scraped_content)
        
        self.assertIsInstance(questions, list)
        mock_client.chat.completions.create.assert_called()
    
    @patch('openai.OpenAI')
    def test_generate_questions_async(self, mock_openai):
        """Test asynchronous question generation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"questions": [{"question": "Test question", "difficulty": "medium"}]}'
        mock_client.chat.completions.create.return_value = mock_response
        
        async def test_async():
            questions = await self.engine.generate_questions_async(self.sample_jd, self.sample_scraped_content)
            return questions
        
        questions = asyncio.run(test_async())
        
        self.assertIsInstance(questions, list)
        mock_client.chat.completions.create.assert_called()
    
    def test_extract_relevant_context(self):
        """Test relevant context extraction."""
        context = self.engine._extract_relevant_context(self.sample_jd, self.sample_scraped_content)
        
        self.assertIsInstance(context, str)
        self.assertGreater(len(context), 0)
        self.assertIn("TechCorp", context)
        self.assertIn("Software Engineer", context)
    
    def test_calculate_content_relevance(self):
        """Test content relevance calculation."""
        content = {
            "title": "Python Best Practices",
            "content": "This article discusses Python best practices for software development...",
            "relevance_score": 0.8
        }
        
        relevance = self.engine._calculate_content_relevance(content, self.sample_jd)
        
        self.assertIsInstance(relevance, float)
        self.assertGreaterEqual(relevance, 0.0)
        self.assertLessEqual(relevance, 1.0)
    
    def test_create_fallback_questions(self):
        """Test fallback question creation."""
        questions = self.engine._create_fallback_questions(self.sample_jd)
        
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)
        
        for question in questions:
            self.assertIn('question', question)
            self.assertIn('difficulty', question)
            self.assertIn('category', question)
    
    @patch('openai.OpenAI')
    def test_generate_difficulty_questions_async(self, mock_openai):
        """Test difficulty-specific question generation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"questions": [{"question": "Test question", "difficulty": "easy"}]}'
        mock_client.chat.completions.create.return_value = mock_response
        
        async def test_async():
            questions = await self.engine._generate_difficulty_questions_async(
                self.sample_jd, "test context", "easy", 2
            )
            return questions
        
        questions = asyncio.run(test_async())
        
        self.assertIsInstance(questions, list)
        mock_client.chat.completions.create.assert_called()
    
    def test_build_prompt(self):
        """Test prompt building."""
        context = "This is test context about software development."
        difficulty = "medium"
        num_questions = 3
        
        prompt = self.engine._build_prompt(self.sample_jd, context, difficulty, num_questions)
        
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
        self.assertIn("TechCorp", prompt)
        self.assertIn("Software Engineer", prompt)
        self.assertIn("medium", prompt)
    
    def test_extract_additional_topics(self):
        """Test additional topics extraction."""
        skills = ["Python", "JavaScript", "React", "AWS"]
        
        topics = self.engine._extract_additional_topics(skills)
        
        self.assertIsInstance(topics, str)
        self.assertGreater(len(topics), 0)
    
    def test_enhance_questions_with_context(self):
        """Test question enhancement with context."""
        questions = [
            {
                "question": "What is Python?",
                "difficulty": "easy",
                "category": "programming"
            }
        ]
        
        enhanced_questions = self.engine.enhance_questions_with_context(
            questions, self.sample_scraped_content
        )
        
        self.assertIsInstance(enhanced_questions, list)
        self.assertEqual(len(enhanced_questions), len(questions))
    
    def test_find_relevant_content(self):
        """Test relevant content finding."""
        question = {
            "question": "What are Python best practices?",
            "difficulty": "medium",
            "category": "programming"
        }
        
        relevant_content = self.engine._find_relevant_content(question, self.sample_scraped_content)
        
        # Should find the Python guide content
        self.assertIsNotNone(relevant_content)
        self.assertIn("Python", relevant_content)
    
    def test_enhance_single_question(self):
        """Test single question enhancement."""
        question = {
            "question": "What is React?",
            "difficulty": "medium",
            "category": "frontend"
        }
        
        relevant_content = "React is a JavaScript library for building user interfaces..."
        
        enhanced_question = self.engine._enhance_single_question(question, relevant_content)
        
        self.assertIsInstance(enhanced_question, dict)
        self.assertIn('question', enhanced_question)
        self.assertIn('difficulty', enhanced_question)
        self.assertIn('category', enhanced_question)
    
    def test_generate_questions_without_client(self):
        """Test question generation without OpenAI client."""
        engine = PromptEngine(Config())  # No API key
        questions = engine.generate_questions(self.sample_jd, self.sample_scraped_content)
        
        self.assertEqual(questions, [])
    
    def test_generate_questions_with_kwargs(self):
        """Test question generation with custom parameters."""
        with patch.object(self.engine, 'generate_questions_async') as mock_async:
            mock_async.return_value = [{"question": "Test", "difficulty": "medium"}]
            
            questions = self.engine.generate_questions(
                self.sample_jd, 
                self.sample_scraped_content,
                temperature=0.7,
                max_tokens=1000
            )
            
            self.assertIsInstance(questions, list)
            mock_async.assert_called_once()
    
    def test_context_compression(self):
        """Test that context compression is working."""
        # Create a large context that should be compressed
        large_context = "This is a very large context. " * 1000
        
        # The context compressor should handle this
        self.assertIsNotNone(self.engine.context_compressor)
        
        # Test that the compressor can process large text
        compressed = self.engine.context_compressor.compress(large_context)
        self.assertIsInstance(compressed, str)
        self.assertLess(len(compressed), len(large_context))


if __name__ == '__main__':
    unittest.main() 