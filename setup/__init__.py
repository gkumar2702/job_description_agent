"""
Setup utilities for JD Agent

This package contains setup and configuration scripts for the JD Agent.
"""

__version__ = "1.0.0"
__author__ = "JD Agent Team"

from .setup_gmail_auth import setup_gmail_auth, test_gmail_connection
from .check_gmail_status import check_gmail_status
from .fix_oauth_access import main as fix_oauth_access
from .setup_service_account import setup_service_account

__all__ = [
    "setup_gmail_auth",
    "test_gmail_connection", 
    "check_gmail_status",
    "fix_oauth_access",
    "setup_service_account"
] 