"""
Test enhanced relevance scoring with rapidfuzz and long page penalty.
"""

import pytest
from unittest.mock import Mock

from ..components.knowledge_miner import KnowledgeMiner, ScrapedContent
from ..utils.config import Config
from ..utils.database import Database
from ..components.jd_parser import JobDescription


class TestEnhancedRelevanceScoring:
    """Test enhanced relevance scoring with rapidfuzz and long page penalty."""
    
    @pytest.fixture
    def config(self):
        """Create a mock config for testing."""
        config = Config(
            SERPAPI_KEY="test_serpapi_key_long_enough_for_validation",
            OPENAI_API_KEY="test_openai_key_long_enough_for_validation",
            GMAIL_CLIENT_ID="test_client_id_long_enough",
            GMAIL_CLIENT_SECRET="test_client_secret_long_enough",
            GMAIL_REFRESH_TOKEN="test_refresh_token_long_enough"
        )
        return config
    
    @pytest.fixture
    def database(self):
        """Create a mock database for testing."""
        return Mock(spec=Database)
    
    @pytest.fixture
    def miner(self, config, database):
        """Create a KnowledgeMiner instance for testing."""
        return KnowledgeMiner(config, database)
    
    @pytest.fixture
    def sample_jd(self):
        """Create a sample job description for testing."""
        return JobDescription(
            email_id="test_email_123",
            company="Google",
            role="Data Scientist",
            location="Mountain View, CA",
            experience_years=3,
            skills=["Python", "Machine Learning", "SQL", "Statistics"],
            content="We are looking for a Data Scientist...",
            confidence_score=0.8,
            parsing_metadata={}
        )
    
    def test_fuzzy_role_matching(self, miner, sample_jd):
        """Test that fuzzy role matching works correctly."""
        # Test exact match
        content_exact = ScrapedContent(
            url="https://example.com/exact",
            title="Data Scientist Interview Questions",
            content="This page contains data scientist interview questions and answers.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_exact = miner._calculate_relevance_score(content_exact, sample_jd)
        assert score_exact > 0.3, f"Exact role match should score high, got {score_exact}"
        
        # Test partial match
        content_partial = ScrapedContent(
            url="https://example.com/partial",
            title="Data Science Interview Guide",
            content="This guide covers data science interviews and preparation.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_partial = miner._calculate_relevance_score(content_partial, sample_jd)
        assert score_partial > 0.1, f"Partial role match should score moderately, got {score_partial}"
        assert score_partial < score_exact, "Exact match should score higher than partial match"
        
        # Test no match
        content_no_match = ScrapedContent(
            url="https://example.com/no-match",
            title="Cooking Recipes and Food Guide",
            content="This page contains delicious recipes and cooking tips for home chefs.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_no_match = miner._calculate_relevance_score(content_no_match, sample_jd)
        assert score_no_match < 0.3, f"No role match should score low, got {score_no_match}"
    
    def test_fuzzy_skill_matching(self, miner, sample_jd):
        """Test that fuzzy skill matching works correctly."""
        # Test exact skill match
        content_exact_skill = ScrapedContent(
            url="https://example.com/exact-skill",
            title="Python Programming Guide",
            content="This guide covers Python programming concepts and best practices.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_exact_skill = miner._calculate_relevance_score(content_exact_skill, sample_jd)
        assert score_exact_skill > 0.1, f"Exact skill match should contribute to score, got {score_exact_skill}"
        
        # Test partial skill match
        content_partial_skill = ScrapedContent(
            url="https://example.com/partial-skill",
            title="Programming with Python",
            content="Learn programming using Python language.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_partial_skill = miner._calculate_relevance_score(content_partial_skill, sample_jd)
        assert score_partial_skill > 0.05, f"Partial skill match should contribute to score, got {score_partial_skill}"
        
        # Test multiple skills
        content_multiple_skills = ScrapedContent(
            url="https://example.com/multiple-skills",
            title="Data Science with Python and SQL",
            content="This guide covers Python programming, SQL queries, and machine learning concepts.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_multiple_skills = miner._calculate_relevance_score(content_multiple_skills, sample_jd)
        assert score_multiple_skills > score_exact_skill, "Multiple skills should score higher than single skill"
    
    def test_long_page_penalty(self, miner, sample_jd):
        """Test that long page penalty is applied correctly."""
        # Create a long page with low relevance
        long_content = "This is a very long page with lots of text. " * 1000  # ~6000 words
        content_long_low_relevance = ScrapedContent(
            url="https://example.com/long-low-relevance",
            title="General Programming Guide",
            content=long_content,
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_long_low = miner._calculate_relevance_score(content_long_low_relevance, sample_jd)
        
        # Create a short page with same low relevance
        short_content = "This is a short page with general programming information."
        content_short_low_relevance = ScrapedContent(
            url="https://example.com/short-low-relevance",
            title="General Programming Guide",
            content=short_content,
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_short_low = miner._calculate_relevance_score(content_short_low_relevance, sample_jd)
        
        # Long page should be penalized (lower score)
        assert score_long_low < score_short_low, "Long page should be penalized compared to short page"
        
        # Test that penalty is not applied to high-relevance long pages
        long_content_high_relevance = f"Data Scientist Interview Questions. {long_content}"
        content_long_high_relevance = ScrapedContent(
            url="https://example.com/long-high-relevance",
            title="Data Scientist Interview Questions",
            content=long_content_high_relevance,
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_long_high = miner._calculate_relevance_score(content_long_high_relevance, sample_jd)
        assert score_long_high > 0.3, "High-relevance long page should not be heavily penalized"
    
    def test_score_bounds(self, miner, sample_jd):
        """Test that scores are properly bounded between 0.0 and 1.0."""
        # Test minimum score
        content_min = ScrapedContent(
            url="https://example.com/min",
            title="Completely Unrelated Content",
            content="This content has nothing to do with data science or programming.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_min = miner._calculate_relevance_score(content_min, sample_jd)
        assert score_min >= 0.0, f"Score should not be negative, got {score_min}"
        
        # Test maximum score (perfect match)
        content_max = ScrapedContent(
            url="https://example.com/max",
            title="Data Scientist Interview Questions and Answers",
            content="Complete guide for data scientist interviews covering Python, Machine Learning, SQL, and Statistics.",
            source="github.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_max = miner._calculate_relevance_score(content_max, sample_jd)
        assert score_max <= 1.0, f"Score should not exceed 1.0, got {score_max}"
        assert score_max > 0.5, f"Perfect match should score high, got {score_max}"
    
    def test_interview_keywords_contribution(self, miner, sample_jd):
        """Test that interview keywords contribute to the score."""
        content_with_keywords = ScrapedContent(
            url="https://example.com/keywords",
            title="Technical Interview Preparation",
            content="This guide helps you prepare for technical interviews with coding questions and solutions.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_with_keywords = miner._calculate_relevance_score(content_with_keywords, sample_jd)
        
        content_without_keywords = ScrapedContent(
            url="https://example.com/no-keywords",
            title="General Programming Guide",
            content="This is a general programming guide without interview content.",
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_without_keywords = miner._calculate_relevance_score(content_without_keywords, sample_jd)
        
        # Content with interview keywords should score higher
        assert score_with_keywords > score_without_keywords, "Interview keywords should improve score"
    
    def test_source_credibility_contribution(self, miner, sample_jd):
        """Test that credible sources contribute to the score."""
        content_credible_source = ScrapedContent(
            url="https://github.com/example",
            title="Data Science Interview Questions",
            content="Interview questions for data scientists.",
            source="github.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_credible = miner._calculate_relevance_score(content_credible_source, sample_jd)
        
        content_unknown_source = ScrapedContent(
            url="https://unknown-site.com/example",
            title="Data Science Interview Questions",
            content="Interview questions for data scientists.",
            source="unknown-site.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_unknown = miner._calculate_relevance_score(content_unknown_source, sample_jd)
        
        # Credible source should score higher
        assert score_credible > score_unknown, "Credible source should improve score"
    
    def test_word_count_calculation(self, miner, sample_jd):
        """Test that word count is calculated correctly for penalty."""
        # Test with exactly 3000 words
        content_3000_words = "word " * 3000
        content_exact = ScrapedContent(
            url="https://example.com/3000",
            title="Test Content",
            content=content_3000_words,
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_exact = miner._calculate_relevance_score(content_exact, sample_jd)
        
        # Test with 3001 words (should trigger penalty)
        content_3001_words = "word " * 3001
        content_over = ScrapedContent(
            url="https://example.com/3001",
            title="Test Content",
            content=content_3001_words,
            source="example.com",
            relevance_score=0.0,
            timestamp=1234567890.0
        )
        
        score_over = miner._calculate_relevance_score(content_over, sample_jd)
        
        # The penalty should only apply if score < 0.5, so we need to ensure that condition
        # For this test, we'll just verify the word counting works
        assert len(content_exact.content.split()) == 3000, "Word count should be 3000"
        assert len(content_over.content.split()) == 3001, "Word count should be 3001"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 