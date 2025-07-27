"""
Test the Pydantic schemas for data validation.
"""

import pytest
from pydantic import ValidationError
from jd_agent.utils.schemas import QA, QAList, JobDescriptionSchema, ScrapedContentSchema, CompressedContentSchema


class TestQASchemas:
    """Test the QA and QAList schemas."""
    
    def test_qa_valid_data(self):
        """Test QA schema with valid data."""
        qa_data = {
            "question": "What is machine learning?",
            "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            "category": "Technical",
            "skills": ["Machine Learning", "AI", "Statistics"]
        }
        
        qa = QA(**qa_data)
        assert qa.question == qa_data["question"]
        assert qa.answer == qa_data["answer"]
        assert qa.category == qa_data["category"]
        assert qa.skills == qa_data["skills"]
    
    def test_qa_invalid_question_length(self):
        """Test QA schema with question that's too short."""
        qa_data = {
            "question": "ML?",  # Too short
            "answer": "Machine learning is a subset of artificial intelligence.",
            "category": "Technical",
            "skills": ["Machine Learning"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            QA(**qa_data)
        
        assert "question" in str(exc_info.value)
        assert "at least 10 characters" in str(exc_info.value)
    
    def test_qa_invalid_answer_length(self):
        """Test QA schema with answer that's too short."""
        qa_data = {
            "question": "What is machine learning?",
            "answer": "AI subset",  # Too short
            "category": "Technical",
            "skills": ["Machine Learning"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            QA(**qa_data)
        
        assert "answer" in str(exc_info.value)
        assert "at least 15 characters" in str(exc_info.value)
    
    def test_qa_missing_fields(self):
        """Test QA schema with missing required fields."""
        qa_data = {
            "question": "What is machine learning?",
            "answer": "Machine learning is a subset of artificial intelligence."
            # Missing category and skills
        }
        
        with pytest.raises(ValidationError) as exc_info:
            QA(**qa_data)
        
        assert "category" in str(exc_info.value)
        assert "skills" in str(exc_info.value)
    
    def test_qa_list_valid_data(self):
        """Test QAList schema with valid data."""
        qa_list_data = {
            "questions": [
                {
                    "question": "What is machine learning?",
                    "answer": "Machine learning is a subset of artificial intelligence.",
                    "category": "Technical",
                    "skills": ["Machine Learning", "AI"]
                },
                {
                    "question": "Explain the difference between supervised and unsupervised learning.",
                    "answer": "Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.",
                    "category": "Technical",
                    "skills": ["Machine Learning", "Data Science"]
                }
            ]
        }
        
        qa_list = QAList(**qa_list_data)
        assert len(qa_list.questions) == 2
        assert qa_list.questions[0].question == "What is machine learning?"
        assert qa_list.questions[1].category == "Technical"
    
    def test_qa_list_empty_questions(self):
        """Test QAList schema with empty questions list."""
        qa_list_data = {
            "questions": []
        }
        
        qa_list = QAList(**qa_list_data)
        assert len(qa_list.questions) == 0
    
    def test_qa_list_invalid_question(self):
        """Test QAList schema with invalid question in list."""
        qa_list_data = {
            "questions": [
                {
                    "question": "ML?",  # Too short (3 characters)
                    "answer": "Machine learning is a subset of artificial intelligence.",
                    "category": "Technical",
                    "skills": ["Machine Learning"]
                }
            ]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            QAList(**qa_list_data)
        
        assert "question" in str(exc_info.value)
        assert "at least 10 characters" in str(exc_info.value)


class TestJobDescriptionSchema:
    """Test the JobDescriptionSchema."""
    
    def test_job_description_valid_data(self):
        """Test JobDescriptionSchema with valid data."""
        jd_data = {
            "company": "Tech Corp",
            "role": "Data Scientist",
            "location": "San Francisco, CA",
            "experience_years": 3,
            "skills": ["Python", "Machine Learning", "SQL"],
            "content": "We are looking for a Data Scientist...",
            "email_id": "email_123",
            "confidence_score": 0.8,
            "parsing_metadata": {"method": "regex"}
        }
        
        jd = JobDescriptionSchema(**jd_data)
        assert jd.company == "Tech Corp"
        assert jd.role == "Data Scientist"
        assert jd.experience_years == 3
        assert jd.confidence_score == 0.8
    
    def test_job_description_invalid_confidence_score(self):
        """Test JobDescriptionSchema with invalid confidence score."""
        jd_data = {
            "company": "Tech Corp",
            "role": "Data Scientist",
            "location": "San Francisco, CA",
            "experience_years": 3,
            "skills": ["Python"],
            "content": "We are looking for a Data Scientist...",
            "email_id": "email_123",
            "confidence_score": 1.5,  # Invalid: > 1.0
            "parsing_metadata": {}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobDescriptionSchema(**jd_data)
        
        assert "confidence_score" in str(exc_info.value)
    
    def test_job_description_negative_experience(self):
        """Test JobDescriptionSchema with negative experience years."""
        jd_data = {
            "company": "Tech Corp",
            "role": "Data Scientist",
            "location": "San Francisco, CA",
            "experience_years": -1,  # Invalid: negative
            "skills": ["Python"],
            "content": "We are looking for a Data Scientist...",
            "email_id": "email_123",
            "confidence_score": 0.8,
            "parsing_metadata": {}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobDescriptionSchema(**jd_data)
        
        assert "experience_years" in str(exc_info.value)


class TestScrapedContentSchema:
    """Test the ScrapedContentSchema."""
    
    def test_scraped_content_valid_data(self):
        """Test ScrapedContentSchema with valid data."""
        content_data = {
            "url": "https://example.com/article",
            "title": "Machine Learning Basics",
            "content": "This article covers the fundamentals of machine learning...",
            "source": "Medium",
            "relevance_score": 0.85,
            "timestamp": 1640995200.0
        }
        
        content = ScrapedContentSchema(**content_data)
        assert content.url == "https://example.com/article"
        assert content.title == "Machine Learning Basics"
        assert content.relevance_score == 0.85
    
    def test_scraped_content_invalid_relevance_score(self):
        """Test ScrapedContentSchema with invalid relevance score."""
        content_data = {
            "url": "https://example.com/article",
            "title": "Machine Learning Basics",
            "content": "This article covers the fundamentals...",
            "source": "Medium",
            "relevance_score": 1.5,  # Invalid: > 1.0
            "timestamp": 1640995200.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ScrapedContentSchema(**content_data)
        
        assert "relevance_score" in str(exc_info.value)


class TestCompressedContentSchema:
    """Test the CompressedContentSchema."""
    
    def test_compressed_content_valid_data(self):
        """Test CompressedContentSchema with valid data."""
        compressed_data = {
            "content": "Compressed content text...",
            "original_count": 10,
            "compressed_count": 5,
            "total_tokens": 1500,
            "relevance_threshold": 0.3,
            "sources_used": ["GitHub", "Medium", "LeetCode"]
        }
        
        compressed = CompressedContentSchema(**compressed_data)
        assert compressed.original_count == 10
        assert compressed.compressed_count == 5
        assert compressed.total_tokens == 1500
        assert compressed.relevance_threshold == 0.3
        assert len(compressed.sources_used) == 3
    
    def test_compressed_content_negative_counts(self):
        """Test CompressedContentSchema with negative counts."""
        compressed_data = {
            "content": "Compressed content text...",
            "original_count": -1,  # Invalid: negative
            "compressed_count": 5,
            "total_tokens": 1500,
            "relevance_threshold": 0.3,
            "sources_used": ["GitHub"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CompressedContentSchema(**compressed_data)
        
        assert "original_count" in str(exc_info.value)


class TestSchemaIntegration:
    """Test schema integration and JSON schema generation."""
    
    def test_qa_json_schema(self):
        """Test that QA schema generates valid JSON schema."""
        json_schema = QA.model_json_schema()
        
        assert "properties" in json_schema
        assert "question" in json_schema["properties"]
        assert "answer" in json_schema["properties"]
        assert "category" in json_schema["properties"]
        assert "skills" in json_schema["properties"]
        
        # Check validation rules
        assert json_schema["properties"]["question"]["minLength"] == 10
        assert json_schema["properties"]["answer"]["minLength"] == 15
    
    def test_qa_list_json_schema(self):
        """Test that QAList schema generates valid JSON schema."""
        json_schema = QAList.model_json_schema()
        
        assert "properties" in json_schema
        assert "questions" in json_schema["properties"]
        assert json_schema["properties"]["questions"]["type"] == "array"
    
    def test_schema_serialization(self):
        """Test that schemas can be serialized and deserialized."""
        qa = QA(
            question="What is Python?",
            answer="Python is a high-level programming language known for its simplicity and readability.",
            category="Technical",
            skills=["Python", "Programming"]
        )
        
        # Serialize to dict
        qa_dict = qa.model_dump()
        assert qa_dict["question"] == "What is Python?"
        assert qa_dict["category"] == "Technical"
        
        # Deserialize from dict
        qa_restored = QA(**qa_dict)
        assert qa_restored.question == qa.question
        assert qa_restored.answer == qa.answer


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 