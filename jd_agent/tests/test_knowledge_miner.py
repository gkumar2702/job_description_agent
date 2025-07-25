"""
Unit tests for KnowledgeMiner component.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ..components.knowledge_miner import KnowledgeMiner
from ..components.jd_parser import JobDescription


class TestKnowledgeMiner:
    """Test cases for KnowledgeMiner."""
    
    @pytest.fixture
    def miner(self):
        """Create a KnowledgeMiner instance for testing."""
        return KnowledgeMiner()
    
    @pytest.fixture
    def sample_jd(self):
        """Sample job description for testing."""
        return JobDescription(
            company="Google",
            role="Software Engineer",
            location="Mountain View, CA",
            experience_years=5,
            skills=["Python", "Java", "JavaScript", "AWS", "Docker"],
            content="We are looking for a Software Engineer with Python and Java experience.",
            email_id="test_123"
        )
    
    def test_identify_source(self, miner):
        """Test source identification from URLs."""
        # Test known sources
        assert miner._identify_source("https://leetcode.com/problems/two-sum") == "LeetCode"
        assert miner._identify_source("https://github.com/user/repo") == "GitHub"
        assert miner._identify_source("https://stackoverflow.com/questions/123") == "Stack Overflow"
        assert miner._identify_source("https://glassdoor.com/Reviews/Google-Reviews") == "Glassdoor"
        
        # Test unknown source
        assert miner._identify_source("https://example.com/page") == "Other"
        
        # Test invalid URL
        assert miner._identify_source("invalid-url") == "Unknown"
    
    def test_build_search_queries(self, miner, sample_jd):
        """Test building search queries from job description."""
        queries = miner._build_search_queries(sample_jd)
        
        # Should contain role-specific queries
        assert any("Software Engineer" in query for query in queries)
        assert any("Google" in query for query in queries)
        
        # Should contain skill-specific queries
        assert any("Python" in query for query in queries)
        assert any("Java" in query for query in queries)
        
        # Should contain experience-specific queries
        assert any("5 years" in query for query in queries)
        
        # Should not exceed limit
        assert len(queries) <= 10
    
    def test_deduplicate_results(self, miner):
        """Test deduplication of search results."""
        results = [
            {'url': 'https://example1.com', 'title': 'Title 1'},
            {'url': 'https://example2.com', 'title': 'Title 2'},
            {'url': 'https://example1.com', 'title': 'Title 1 Duplicate'},  # Duplicate URL
            {'url': 'https://example3.com', 'title': 'Title 3'},
        ]
        
        deduplicated = miner._deduplicate_results(results)
        
        # Should remove duplicate URL
        assert len(deduplicated) == 3
        urls = [r['url'] for r in deduplicated]
        assert 'https://example1.com' in urls
        assert 'https://example2.com' in urls
        assert 'https://example3.com' in urls
    
    def test_extract_questions_from_content(self, miner):
        """Test extracting questions from content."""
        content = """
        Here are some interview questions:
        
        What is the difference between a list and a tuple in Python?
        How would you implement a binary search tree?
        Explain the concept of dependency injection.
        
        These are not questions.
        This is just regular text.
        """
        
        questions = miner.extract_questions_from_content(content)
        
        assert len(questions) >= 2
        assert any("list and a tuple" in q for q in questions)
        assert any("binary search tree" in q for q in questions)
        assert any("dependency injection" in q for q in questions)
    
    def test_filter_relevant_content(self, miner, sample_jd):
        """Test filtering content based on relevance."""
        # Relevant content
        relevant_content = """
        Python interview questions for software engineers.
        Technical interview preparation for Google.
        Coding problems and solutions.
        """
        assert miner.filter_relevant_content(relevant_content, sample_jd) is True
        
        # Irrelevant content
        irrelevant_content = """
        Cooking recipes and food preparation.
        Gardening tips and plant care.
        Travel destinations and vacation planning.
        """
        assert miner.filter_relevant_content(irrelevant_content, sample_jd) is False
    
    @patch('requests.Session.get')
    def test_scrape_url_success(self, mock_get, miner):
        """Test successful URL scraping."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body><p>This is test content</p></body></html>'
        mock_get.return_value = mock_response
        
        content = miner._scrape_url("https://example.com")
        
        assert content is not None
        assert "test content" in content
        mock_get.assert_called_once_with("https://example.com", timeout=10)
    
    @patch('requests.Session.get')
    def test_scrape_url_failure(self, mock_get, miner):
        """Test URL scraping failure."""
        # Mock failed response
        mock_get.side_effect = Exception("Connection error")
        
        content = miner._scrape_url("https://example.com")
        
        assert content is None
    
    @patch('requests.Session.get')
    def test_scrape_url_large_content(self, mock_get, miner):
        """Test scraping URL with large content."""
        # Mock response with large content
        large_content = "Test content " * 1000  # Very large content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = f'<html><body><p>{large_content}</p></body></html>'.encode()
        mock_get.return_value = mock_response
        
        content = miner._scrape_url("https://example.com")
        
        assert content is not None
        assert len(content) <= 10000  # Should be truncated
        assert content.endswith("...")
    
    def test_calculate_similarity(self, miner):
        """Test similarity calculation between questions."""
        # Identical questions
        q1 = "What is Python?"
        q2 = "What is Python?"
        assert miner._calculate_similarity(q1, q2) == 1.0
        
        # Similar questions
        q1 = "What is the difference between a list and a tuple?"
        q2 = "What is the difference between a tuple and a list?"
        similarity = miner._calculate_similarity(q1, q2)
        assert similarity > 0.5
        
        # Different questions
        q1 = "What is Python?"
        q2 = "How do you cook pasta?"
        similarity = miner._calculate_similarity(q1, q2)
        assert similarity < 0.5
        
        # Empty questions
        assert miner._calculate_similarity("", "test") == 0.0
        assert miner._calculate_similarity("test", "") == 0.0
    
    @patch('serpapi.GoogleSearch')
    def test_perform_search_success(self, mock_search, miner):
        """Test successful search performance."""
        # Mock search results
        mock_search_instance = Mock()
        mock_search_instance.get_dict.return_value = {
            'organic_results': [
                {
                    'title': 'Test Result 1',
                    'link': 'https://example1.com',
                    'snippet': 'This is a test snippet'
                },
                {
                    'title': 'Test Result 2',
                    'link': 'https://example2.com',
                    'snippet': 'Another test snippet'
                }
            ]
        }
        mock_search.return_value = mock_search_instance
        
        results = miner._perform_search("test query")
        
        assert len(results) == 2
        assert results[0]['title'] == 'Test Result 1'
        assert results[1]['title'] == 'Test Result 2'
    
    @patch('serpapi.GoogleSearch')
    def test_perform_search_failure(self, mock_search, miner):
        """Test search failure handling."""
        mock_search.side_effect = Exception("API error")
        
        results = miner._perform_search("test query")
        
        assert results == []
    
    def test_scrape_content(self, miner):
        """Test scraping content from multiple URLs."""
        search_results = [
            {'url': 'https://example1.com', 'title': 'Title 1'},
            {'url': 'https://example2.com', 'title': 'Title 2'},
        ]
        
        with patch.object(miner, '_scrape_url') as mock_scrape:
            mock_scrape.side_effect = ['Content 1', 'Content 2']
            
            scraped = miner.scrape_content(search_results)
            
            assert len(scraped) == 2
            assert scraped[0]['content'] == 'Content 1'
            assert scraped[1]['content'] == 'Content 2'
    
    def test_scrape_content_with_failures(self, miner):
        """Test scraping content with some URL failures."""
        search_results = [
            {'url': 'https://example1.com', 'title': 'Title 1'},
            {'url': 'https://example2.com', 'title': 'Title 2'},
            {'url': 'https://example3.com', 'title': 'Title 3'},
        ]
        
        with patch.object(miner, '_scrape_url') as mock_scrape:
            mock_scrape.side_effect = ['Content 1', None, 'Content 3']  # Second URL fails
            
            scraped = miner.scrape_content(search_results)
            
            assert len(scraped) == 2  # Only successful scrapes
            assert scraped[0]['content'] == 'Content 1'
            assert scraped[1]['content'] == 'Content 3' 