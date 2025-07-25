"""
Unit tests for JDParser component.
"""

import pytest
from unittest.mock import Mock, patch
from ..components.jd_parser import JDParser, JobDescription


class TestJDParser:
    """Test cases for JDParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a JDParser instance for testing."""
        with patch('spacy.load'):
            return JDParser()
    
    @pytest.fixture
    def sample_email_data(self):
        """Sample email data for testing."""
        return {
            'id': 'test_email_123',
            'subject': 'Software Engineer Position at Google',
            'body': '''
            We are looking for a Senior Software Engineer to join our team at Google.
            
            Requirements:
            - 5+ years of experience in software development
            - Proficiency in Python, Java, and JavaScript
            - Experience with cloud platforms (AWS, GCP)
            - Knowledge of machine learning and data science
            - Location: Mountain View, CA
            
            Responsibilities:
            - Develop scalable software solutions
            - Collaborate with cross-functional teams
            - Mentor junior developers
            '''
        }
    
    def test_parse_valid_job_description(self, parser, sample_email_data):
        """Test parsing a valid job description."""
        jd = parser.parse(sample_email_data)
        
        assert jd is not None
        assert jd.company == "Google"
        assert "Software Engineer" in jd.role
        assert jd.location == "Mountain View, CA"
        assert jd.experience_years == 5
        assert "Python" in jd.skills
        assert "Java" in jd.skills
        assert "JavaScript" in jd.skills
        assert jd.email_id == "test_email_123"
    
    def test_parse_invalid_email_data(self, parser):
        """Test parsing invalid email data."""
        invalid_data = {
            'id': 'test_email_123',
            'subject': 'Random email',
            'body': 'This is just a regular email with no job information.'
        }
        
        jd = parser.parse(invalid_data)
        assert jd is None
    
    def test_extract_company(self, parser):
        """Test company name extraction."""
        text = "Join our team at Microsoft as a Software Engineer"
        company = parser._extract_company(text)
        assert "Microsoft" in company
    
    def test_extract_role(self, parser):
        """Test job role extraction."""
        text = "We are hiring a Senior Data Scientist for our team"
        role = parser._extract_role(text)
        assert "Data Scientist" in role
    
    def test_extract_location(self, parser):
        """Test location extraction."""
        text = "Position based in San Francisco, CA"
        location = parser._extract_location(text)
        assert "San Francisco" in location
    
    def test_extract_experience(self, parser):
        """Test experience extraction."""
        text = "Requires 3-5 years of experience in software development"
        experience = parser._extract_experience(text)
        assert experience == 4  # Average of 3-5
    
    def test_extract_skills(self, parser):
        """Test skills extraction."""
        text = "Skills required: Python, React, AWS, Docker"
        skills = parser._extract_skills(text)
        assert "Python" in skills
        assert "React" in skills
        assert "AWS" in skills
        assert "Docker" in skills
    
    def test_validate_jd_valid(self, parser):
        """Test validation of valid job description."""
        jd = JobDescription(
            company="Test Company",
            role="Software Engineer",
            location="Test Location",
            experience_years=3,
            skills=["Python", "Java"],
            content="This is a valid job description with sufficient content.",
            email_id="test_123"
        )
        
        assert parser.validate_jd(jd) is True
    
    def test_validate_jd_invalid(self, parser):
        """Test validation of invalid job description."""
        # Test with missing company
        jd1 = JobDescription(
            company="",
            role="Software Engineer",
            location="Test Location",
            experience_years=3,
            skills=["Python"],
            content="Valid content",
            email_id="test_123"
        )
        assert parser.validate_jd(jd1) is False
        
        # Test with missing role
        jd2 = JobDescription(
            company="Test Company",
            role="",
            location="Test Location",
            experience_years=3,
            skills=["Python"],
            content="Valid content",
            email_id="test_123"
        )
        assert parser.validate_jd(jd2) is False
        
        # Test with insufficient content
        jd3 = JobDescription(
            company="Test Company",
            role="Software Engineer",
            location="Test Location",
            experience_years=3,
            skills=["Python"],
            content="Short",
            email_id="test_123"
        )
        assert parser.validate_jd(jd3) is False
    
    def test_normalize_question(self, parser):
        """Test question normalization."""
        question = "What is the difference between a List and a Tuple?"
        normalized = parser._normalize_question(question)
        assert normalized == "what is the difference between a list and a tuple"
    
    def test_parse_with_spacy_fallback(self, parser):
        """Test parsing when spaCy is not available."""
        parser.nlp = None  # Simulate spaCy not being available
        
        text = "Join our team at Apple as a Software Engineer"
        company = parser._extract_company(text)
        # Should still work with regex patterns
        assert company != ""
    
    def test_extract_skills_from_list(self, parser):
        """Test extracting skills from bullet point lists."""
        text = """
        Requirements:
        • Python programming
        • JavaScript development
        • AWS cloud services
        • Docker containerization
        """
        skills = parser._extract_skills(text)
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "AWS" in skills
        assert "Docker" in skills 