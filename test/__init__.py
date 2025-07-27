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
from .test_enhanced_email_collector import test_enhanced_email_collector
from .test_enhanced_jd_parser import test_enhanced_parser, test_company_extraction, test_role_extraction
from .check_pipeline_results import check_database, check_exports, test_email_collector, test_jd_parser, check_storage_pipeline, suggest_improvements
from .run_pipeline_and_check_results import run_email_collection, run_jd_parsing, check_database_after_pipeline, check_all_storage_locations, show_sample_results

__all__ = [
    "test_basic_functionality",
    "test_email_collector",
    "test_email_search_query",
    "analyze_emails", 
    "test_search_queries",
    "test_full_pipeline",
    "test_jd_detection",
    "test_enhanced_email_collector",
    "test_enhanced_parser",
    "test_company_extraction",
    "test_role_extraction",
    "check_database",
    "check_exports",
    "test_email_collector",
    "test_jd_parser",
    "check_storage_pipeline",
    "suggest_improvements",
    "run_email_collection",
    "run_jd_parsing",
    "check_database_after_pipeline",
    "check_all_storage_locations",
    "show_sample_results"
] 