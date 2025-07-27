"""
Test utilities for JD Agent

This package contains test scripts for the JD Agent components.
"""

__version__ = "1.0.0"
__author__ = "JD Agent Team"

from .test_demo import test_basic_functionality
from .test_email_collector import test_email_collector, test_email_search_query
from .test_email_details import analyze_emails, test_search_queries
from .test_full_pipeline import test_full_pipeline, test_jd_detection

__all__ = [
    "test_basic_functionality",
    "test_email_collector",
    "test_email_search_query",
    "analyze_emails", 
    "test_search_queries",
    "test_full_pipeline",
    "test_jd_detection"
] 