"""
Pydantic schemas for structured data validation.

This module contains Pydantic models for validating question-answer structures
and other data formats used throughout the JD Agent application.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any


class Question(BaseModel):
    """Question model for interview questions."""
    difficulty: str
    question: str = Field(..., min_length=10)
    answer: str
    category: str = "Technical"
    skills: List[str]
    source: str = "Generated"
    relevance_score: Optional[float] = None


class QA(BaseModel):
    """Question-Answer pair with validation."""
    question: str = Field(..., min_length=10, description="The interview question text")
    answer: str = Field(..., min_length=15, description="A detailed answer or explanation")
    category: str = Field(..., description="The category of the question (e.g., Technical, Behavioral, Problem-Solving, System Design)")
    skills: List[str] = Field(..., description="List of skills being tested by this question")


class QAList(BaseModel):
    """List of question-answer pairs."""
    questions: List[QA] = Field(..., description="List of interview questions and answers")


# Additional schemas for future use
class JobDescriptionSchema(BaseModel):
    """Structured job description data."""
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job role/title")
    location: str = Field(..., description="Job location")
    experience_years: int = Field(..., ge=0, description="Required years of experience")
    skills: List[str] = Field(..., description="Required skills")
    content: str = Field(..., description="Full job description content")
    email_id: str = Field(..., description="Associated email ID")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Parsing confidence score")
    parsing_metadata: dict = Field(default_factory=dict, description="Metadata about parsing process")

    def model_json_schema(self, **kwargs: Any) -> dict[str, Any]:
        """Get JSON schema for the model."""
        return super().model_json_schema(**kwargs)


class ScrapedContentSchema(BaseModel):
    """Structured scraped content data."""
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Main content text")
    source: str = Field(..., description="Source name (e.g., GitHub, Medium)")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    timestamp: float = Field(..., description="Timestamp when content was scraped")


class CompressedContentSchema(BaseModel):
    """Structured compressed content data."""
    content: str = Field(..., description="Compressed content text")
    original_count: int = Field(..., ge=0, description="Number of original content pieces")
    compressed_count: int = Field(..., ge=0, description="Number of compressed content pieces")
    total_tokens: int = Field(..., ge=0, description="Total tokens in compressed content")
    relevance_threshold: float = Field(..., ge=0.0, le=1.0, description="Minimum relevance threshold used")
    sources_used: List[str] = Field(..., description="List of sources included in compression") 