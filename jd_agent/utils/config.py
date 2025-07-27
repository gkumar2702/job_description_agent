"""
Configuration management for JD Agent.
"""

import os
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration class for JD Agent application with Pydantic validation."""
    
    # Gmail API Configuration
    GMAIL_CLIENT_ID: str = Field(default="", description="Gmail API Client ID")
    GMAIL_CLIENT_SECRET: str = Field(default="", description="Gmail API Client Secret")
    GMAIL_REFRESH_TOKEN: str = Field(default="", description="Gmail API Refresh Token")
    
    # Search API Configuration
    SERPAPI_KEY: str = Field(default="", description="SerpAPI Key")
    GOOGLE_CSE_ID: str = Field(default="", description="Google Custom Search Engine ID")
    GOOGLE_API_KEY: str = Field(default="", description="Google API Key")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="OpenAI Model to use")
    
    # Database Configuration
    DATABASE_PATH: str = Field(default="./data/jd_agent.db", description="Database file path")
    
    # Application Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    MAX_SEARCH_RESULTS: int = Field(default=20, ge=1, le=100, description="Maximum search results")
    MAX_TOKENS: int = Field(default=4000, ge=1, le=32000, description="Maximum tokens for API calls")
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for AI responses")
    
    # Email search configuration
    EMAIL_SEARCH_QUERY: str = Field(
        default='label:"inbox" AND ("has:attachment" OR "Job Description")',
        description="Gmail search query for job descriptions"
    )
    
    # Search sources configuration - must not be empty
    SEARCH_SOURCES: List[str] = Field(
        default=[
            "Glassdoor",
            "LeetCode", 
            "GitHub",
            "Stack Overflow",
            "InterviewBit",
            "HackerRank"
        ],
        description="List of search sources for job information"
    )
    
    @field_validator('SEARCH_SOURCES')
    @classmethod
    def validate_search_sources_not_empty(cls, v):
        """Ensure search sources list is not empty."""
        if not v:
            raise ValueError('SEARCH_SOURCES list cannot be empty')
        return v
    
    @field_validator('SERPAPI_KEY')
    @classmethod
    def validate_serpapi_key(cls, v):
        """Validate SerpAPI key format if provided."""
        if v and len(v) < 10:  # Basic length check
            raise ValueError('SERPAPI_KEY should be at least 10 characters long')
        return v
    
    @field_validator('OPENAI_API_KEY')
    @classmethod
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format if provided."""
        if v and len(v) < 10:  # Basic length check
            raise ValueError('OPENAI_API_KEY should be at least 10 characters long')
        return v
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Create Config instance from environment variables.
        
        Returns:
            Config: Configuration instance
        """
        return cls(
            GMAIL_CLIENT_ID=os.getenv("GMAIL_CLIENT_ID", ""),
            GMAIL_CLIENT_SECRET=os.getenv("GMAIL_CLIENT_SECRET", ""),
            GMAIL_REFRESH_TOKEN=os.getenv("GMAIL_REFRESH_TOKEN", ""),
            SERPAPI_KEY=os.getenv("SERPAPI_KEY", ""),
            GOOGLE_CSE_ID=os.getenv("GOOGLE_CSE_ID", ""),
            GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY", ""),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
            OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-4o"),
            DATABASE_PATH=os.getenv("DATABASE_PATH", "./data/jd_agent.db"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            MAX_SEARCH_RESULTS=int(os.getenv("MAX_SEARCH_RESULTS", "20")),
            MAX_TOKENS=int(os.getenv("MAX_TOKENS", "4000")),
            TEMPERATURE=float(os.getenv("TEMPERATURE", "0.7")),
            EMAIL_SEARCH_QUERY=os.getenv(
                "EMAIL_SEARCH_QUERY", 
                'label:"inbox" AND ("has:attachment" OR "Job Description")'
            ),
            SEARCH_SOURCES=[
                "Glassdoor",
                "LeetCode", 
                "GitHub",
                "Stack Overflow",
                "InterviewBit",
                "HackerRank"
            ]
        )
    
    def validate_required(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_fields = [
            "GMAIL_CLIENT_ID",
            "GMAIL_CLIENT_SECRET", 
            "GMAIL_REFRESH_TOKEN",
            "SERPAPI_KEY",
            "OPENAI_API_KEY"
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            print("Please check your .env file and ensure all required fields are set.")
            return False
        
        return True
    
    def get_database_url(self) -> str:
        """
        Get the database URL for SQLite.
        
        Returns:
            str: Database URL
        """
        return f"sqlite:///{self.DATABASE_PATH}"
    
    def get_export_dir(self) -> str:
        """
        Get the export directory path.
        
        Returns:
            str: Export directory path
        """
        return "./data/exports"


# Create a global config instance for backward compatibility
config = Config.from_env() 