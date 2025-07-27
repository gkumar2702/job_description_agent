"""
Configuration management for JD Agent.
"""

import os
from typing import Any, Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration class for JD Agent application."""
    
    # API Keys
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    SERPAPI_KEY: str = Field(default="", description="SerpAPI key")
    GMAIL_REFRESH_TOKEN: str = Field(default="", description="Gmail refresh token")
    
    # OpenAI Configuration
    OPENAI_MODEL: str = Field(default="gpt-4o", description="OpenAI model to use")
    MAX_TOKENS: int = Field(default=2000, description="Maximum tokens for OpenAI responses")
    TEMPERATURE: float = Field(default=0.3, description="Temperature for OpenAI responses (0.0-2.0)")
    TOP_P: float = Field(default=0.9, description="Top-p sampling for OpenAI responses (0.0-1.0)")
    
    # Database
    DATABASE_PATH: str = Field(default="./data/jd_agent.db", description="SQLite database path")
    
    # Export settings
    EXPORT_DIR: str = Field(default="./exports", description="Export directory")
    
    # Search sources (from constants)
    SEARCH_SOURCES: dict[str, list[str]] = Field(
        default={
            "leetcode": ["leetcode.com"],
            "hackerrank": ["hackerrank.com"],
            "geeksforgeeks": ["geeksforgeeks.org"],
            "medium": ["medium.com"],
            "github": ["github.com"],
            "reddit": ["reddit.com"],
            "stackoverflow": ["stackoverflow.com"],
            "kaggle": ["kaggle.com"],
            "stratascratch": ["stratascratch.com"],
            "w3schools": ["w3schools.com"]
        },
        description="Search sources for knowledge mining"
    )
    
    # Direct sources (from constants)
    ALLOWED_DIRECT_SOURCES: dict[str, list[str]] = Field(
        default={
            "leetcode": [
                "https://leetcode.com/problems/",
                "https://leetcode.com/discuss/"
            ],
            "hackerrank": [
                "https://www.hackerrank.com/challenges/",
                "https://www.hackerrank.com/domains/"
            ],
            "geeksforgeeks": [
                "https://www.geeksforgeeks.org/",
                "https://www.geeksforgeeks.org/tag/interview-questions/"
            ],
            "medium": [
                "https://medium.com/tag/interview-questions",
                "https://medium.com/tag/technical-interview"
            ],
            "github": [
                "https://github.com/topics/interview-questions",
                "https://github.com/topics/technical-interview"
            ]
        },
        description="Direct sources for knowledge mining"
    )
    
    # Interview keywords (from constants)
    INTERVIEW_KEYWORDS: list[str] = Field(
        default=[
            "interview", "question", "technical", "coding", "algorithm",
            "data structure", "system design", "behavioral", "whiteboard",
            "leetcode", "hackerrank", "geeksforgeeks", "practice", "problem"
        ],
        description="Keywords related to interview questions"
    )
    
    # Credible sources (from constants)
    CREDIBLE_SOURCES: list[str] = Field(
        default=[
            "leetcode.com", "hackerrank.com", "geeksforgeeks.org",
            "medium.com", "github.com", "stackoverflow.com", "kaggle.com"
        ],
        description="Credible sources for interview content"
    )
    
    @field_validator('SEARCH_SOURCES')
    @classmethod
    def validate_search_sources_not_empty(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        """Validate that search sources are not empty."""
        if not v:
            raise ValueError("SEARCH_SOURCES cannot be empty")
        return v
    
    @field_validator('SERPAPI_KEY')
    @classmethod
    def validate_serpapi_key(cls, v: str) -> str:
        """Validate SerpAPI key format."""
        if v and len(v) < 10:
            raise ValueError("SERPAPI_KEY must be at least 10 characters long")
        return v
    
    @field_validator('OPENAI_API_KEY')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key format."""
        if v and len(v) < 10:
            raise ValueError("OPENAI_API_KEY must be at least 10 characters long")
        return v
    
    def validate_required(self) -> None:
        """Validate that required fields are set."""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not self.SERPAPI_KEY:
            raise ValueError("SERPAPI_KEY is required")
    
    def get_database_url(self) -> str:
        """Get database URL."""
        return f"sqlite:///{self.DATABASE_PATH}"
    
    def get_export_dir(self) -> str:
        """Get export directory path."""
        return self.EXPORT_DIR
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create Config instance from environment variables."""
        return cls(
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
            SERPAPI_KEY=os.getenv("SERPAPI_KEY", ""),
            GMAIL_REFRESH_TOKEN=os.getenv("GMAIL_REFRESH_TOKEN", ""),
            DATABASE_PATH=os.getenv("DATABASE_PATH", "./data/jd_agent.db"),
            EXPORT_DIR=os.getenv("EXPORT_DIR", "./exports")
        )


# Global config instance for backward compatibility
config = Config.from_env() 