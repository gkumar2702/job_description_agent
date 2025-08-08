#!/usr/bin/env python3
"""
Tests for QuestionBank component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import json
import tempfile
import shutil
from typing import Dict, Any, List

# Add the parent directory to the path to import jd_agent
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jd_agent.components.question_bank import QuestionBank
from jd_agent.components.jd_parser import JobDescription
from jd_agent.components.scoring_strategies import HeuristicScorer
from jd_agent.utils.config import Config
from jd_agent.utils.schemas import Question


class TestQuestionBank(unittest.TestCase):
    """Test cases for QuestionBank component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        self.scorer = HeuristicScorer()
        
        # Create temporary directory for exports
        self.temp_dir = tempfile.mkdtemp()
        self.config.EXPORT_DIR = self.temp_dir
        
        self.question_bank = QuestionBank(self.config, self.scorer)
        
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
        
        # Sample questions
        self.sample_questions = [
            {
                "question": "What is Python?",
                "answer": "Python is a programming language.",
                "difficulty": "easy",
                "category": "programming",
                "relevance_score": 0.8
            },
            {
                "question": "Explain React hooks.",
                "answer": "React hooks are functions that allow you to use state and other React features.",
                "difficulty": "medium",
                "category": "frontend",
                "relevance_score": 0.9
            },
            {
                "question": "What is AWS?",
                "answer": "AWS is Amazon Web Services, a cloud computing platform.",
                "difficulty": "medium",
                "category": "cloud",
                "relevance_score": 0.7
            }
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test QuestionBank initialization."""
        self.assertIsNotNone(self.question_bank)
        self.assertEqual(self.question_bank.questions, [])
        self.assertEqual(self.question_bank.scorer, self.scorer)
        self.assertEqual(self.question_bank.export_dir, self.temp_dir)
    
    def test_add_questions(self):
        """Test adding questions to the bank."""
        initial_count = len(self.question_bank.questions)
        
        self.question_bank.add_questions(self.sample_questions)
        
        self.assertEqual(len(self.question_bank.questions), initial_count + len(self.sample_questions))
        
        # Check that questions were converted to Question objects
        for question in self.question_bank.questions:
            self.assertIsInstance(question, Question)
    
    def test_add_questions_with_invalid_data(self):
        """Test adding questions with invalid data."""
        invalid_questions = [
            {
                "question": "Valid question",
                "answer": "Valid answer",
                "difficulty": "easy",
                "category": "test"
                # Missing relevance_score
            },
            {
                "question": "Another question",
                "difficulty": "medium"
                # Missing required fields
            }
        ]
        
        initial_count = len(self.question_bank.questions)
        
        self.question_bank.add_questions(invalid_questions)
        
        # Should only add valid questions
        self.assertGreaterEqual(len(self.question_bank.questions), initial_count)
    
    def test_deduplicate_questions(self):
        """Test question deduplication."""
        # Add duplicate questions
        duplicate_questions = self.sample_questions + [
            {
                "question": "What is Python?",  # Duplicate
                "answer": "Python is a programming language.",
                "difficulty": "easy",
                "category": "programming",
                "relevance_score": 0.8
            },
            {
                "question": "What is Python programming?",  # Similar
                "answer": "Python is a programming language.",
                "difficulty": "easy",
                "category": "programming",
                "relevance_score": 0.8
            }
        ]
        
        self.question_bank.add_questions(duplicate_questions)
        
        before_count = len(self.question_bank.questions)
        deduplicated = self.question_bank.deduplicate_questions()
        
        self.assertIsInstance(deduplicated, list)
        self.assertLessEqual(len(deduplicated), before_count)
    
    def test_remove_exact_duplicates(self):
        """Test exact duplicate removal."""
        questions = [
            Question(question="Q1", answer="A1", difficulty="easy", category="test", relevance_score=0.8),
            Question(question="Q1", answer="A1", difficulty="easy", category="test", relevance_score=0.8),
            Question(question="Q2", answer="A2", difficulty="easy", category="test", relevance_score=0.8)
        ]
        
        unique_questions = self.question_bank._remove_exact_duplicates(questions)
        
        self.assertEqual(len(unique_questions), 2)
        self.assertEqual(unique_questions[0].question, "Q1")
        self.assertEqual(unique_questions[1].question, "Q2")
    
    def test_normalize_question(self):
        """Test question normalization."""
        question = "What is Python?"
        normalized = self.question_bank._normalize_question(question)
        
        self.assertIsInstance(normalized, str)
        self.assertIn("python", normalized.lower())
    
    def test_remove_similar_questions(self):
        """Test similar question removal."""
        questions = [
            Question(question="What is Python?", answer="A1", difficulty="easy", category="test", relevance_score=0.8),
            Question(question="What is Python programming?", answer="A2", difficulty="easy", category="test", relevance_score=0.8),
            Question(question="What is JavaScript?", answer="A3", difficulty="easy", category="test", relevance_score=0.8)
        ]
        
        unique_questions = self.question_bank._remove_similar_questions(questions)
        
        self.assertLessEqual(len(unique_questions), len(questions))
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        question1 = "What is Python?"
        question2 = "What is Python programming?"
        question3 = "What is JavaScript?"
        
        similarity_12 = self.question_bank._calculate_similarity(question1, question2)
        similarity_13 = self.question_bank._calculate_similarity(question1, question3)
        
        self.assertIsInstance(similarity_12, int)
        self.assertIsInstance(similarity_13, int)
        self.assertGreater(similarity_12, similarity_13)  # Python questions should be more similar
    
    def test_score_questions(self):
        """Test question scoring."""
        self.question_bank.add_questions(self.sample_questions)
        
        scored_questions = self.question_bank.score_questions(self.sample_jd)
        
        self.assertIsInstance(scored_questions, list)
        self.assertEqual(len(scored_questions), len(self.sample_questions))
        
        for question in scored_questions:
            self.assertIn('question', question)
            self.assertIn('score', question)
            self.assertIsInstance(question['score'], float)
    
    def test_export_questions_sync(self):
        """Test synchronous question export (PDF-only)."""
        result = self.question_bank.export_questions_sync(
            self.sample_jd,
            self.sample_questions,
        )
        self.assertIsInstance(result, dict)
        self.assertIn('pdf', result)
        self.assertTrue(os.path.exists(result['pdf']))
    
    def test_export_markdown(self):
        """Keep legacy markdown export available for direct calls (if needed)."""
        filename = self.question_bank._export_markdown(
            self.sample_questions,
            self.sample_jd,
            "test_export"
        )
        self.assertIsInstance(filename, str)
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.md'))
    
    def test_export_csv(self):
        """Keep legacy CSV export available for direct calls (if needed)."""
        filename = self.question_bank._export_csv(
            self.sample_questions, 
            self.sample_jd, 
            "test_export"
        )
        
        self.assertIsInstance(filename, str)
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.csv'))
    
    def test_export_json(self):
        """Keep legacy JSON export available for direct calls (if needed)."""
        filename = self.question_bank._export_json(
            self.sample_questions, 
            self.sample_jd, 
            "test_export"
        )
        
        self.assertIsInstance(filename, str)
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.json'))
    
    def test_export_xlsx(self):
        """Keep legacy Excel export available for direct calls (if needed)."""
        filename = self.question_bank._export_xlsx(
            self.sample_questions, 
            self.sample_jd, 
            "test_export"
        )
        
        self.assertIsInstance(filename, str)
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.xlsx'))
    
    def test_get_question_statistics(self):
        """Test question statistics."""
        self.question_bank.add_questions(self.sample_questions)
        
        stats = self.question_bank.get_question_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_questions', stats)
        self.assertIn('difficulty_distribution', stats)
        self.assertIn('category_distribution', stats)
        self.assertEqual(stats['total_questions'], len(self.sample_questions))
    
    def test_get_questions_by_difficulty(self):
        """Test questions by difficulty."""
        self.question_bank.add_questions(self.sample_questions)
        
        difficulty_stats = self.question_bank.get_questions_by_difficulty()
        
        self.assertIsInstance(difficulty_stats, dict)
        self.assertIn('easy', difficulty_stats)
        self.assertIn('medium', difficulty_stats)
    
    def test_get_average_relevance_score(self):
        """Test average relevance score calculation."""
        self.question_bank.add_questions(self.sample_questions)
        
        avg_score = self.question_bank.get_average_relevance_score()
        
        self.assertIsInstance(avg_score, float)
        self.assertGreaterEqual(avg_score, 0.0)
        self.assertLessEqual(avg_score, 1.0)
    
    def test_get_export_files(self):
        """Test getting export files (currently returns an empty list)."""
        export_files = self.question_bank.get_export_files()
        self.assertIsInstance(export_files, list)
    
    async def test_export_questions_async(self):
        """Test asynchronous question export (PDF-only)."""
        result = await self.question_bank.export_questions_async(
            self.sample_jd,
            self.sample_questions,
        )
        self.assertIsInstance(result, dict)
        self.assertIn('pdf', result)
        self.assertTrue(os.path.exists(result['pdf']))


if __name__ == '__main__':
    unittest.main() 