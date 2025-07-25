"""
Configuration management for JD Agent.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for JD Agent application."""
    
    # Gmail API Configuration
    GMAIL_CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET", "")
    GMAIL_REFRESH_TOKEN: str = os.getenv("GMAIL_REFRESH_TOKEN", "")
    
    # Search API Configuration
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/jd_agent.db")
    
    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "20"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Email search configuration
    EMAIL_SEARCH_QUERY: str = os.getenv(
        "EMAIL_SEARCH_QUERY", 
        'label:"inbox" AND ("has:attachment" OR "Job Description")'
    )
    
    # Search sources configuration
    SEARCH_SOURCES: list = [
        "Glassdoor",
        "LeetCode", 
        "GitHub",
        "Stack Overflow",
        "InterviewBit",
        "HackerRank"
    ]
    
    @classmethod
    def validate(cls) -> bool:
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
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            print("Please check your .env file and ensure all required fields are set.")
            return False
        
        return True
    
    @classmethod
    def get_database_url(cls) -> str:
        """
        Get the database URL for SQLite.
        
        Returns:
            str: Database URL
        """
        return f"sqlite:///{cls.DATABASE_PATH}"
    
    @classmethod
    def get_export_dir(cls) -> str:
        """
        Get the export directory path.
        
        Returns:
            str: Export directory path
        """
        return "./data/exports" 