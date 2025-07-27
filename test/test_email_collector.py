#!/usr/bin/env python3
"""
Test Email Collector Functionality

This script tests the email collector to fetch job description emails from Gmail.
"""

import sys
from jd_agent.components.email_collector import EmailCollector
from jd_agent.utils.config import Config

def test_email_collector():
    """Test the email collector functionality."""
    
    print("📧 Testing Email Collector")
    print("=" * 50)
    
    try:
        # Initialize the email collector
        print("1. Initializing Email Collector...")
        collector = EmailCollector()
        
        if not collector.service:
            print("❌ Email collector service not available")
            return False
        
        print("✅ Email collector initialized successfully")
        
        # Test fetching emails from last 7 days
        print("\n2. Fetching job description emails (last 7 days)...")
        emails = collector.fetch_jd_emails(days_back=7)
        
        print(f"✅ Found {len(emails)} potential job description emails")
        
        if emails:
            print("\n📋 Email Summary:")
            for i, email in enumerate(emails[:5], 1):  # Show first 5 emails
                subject = email.get('subject', 'No subject')
                sender = email.get('from', 'Unknown sender')
                date = email.get('date', 'Unknown date')
                
                print(f"   {i}. {subject}")
                print(f"      From: {sender}")
                print(f"      Date: {date}")
                print()
            
            if len(emails) > 5:
                print(f"   ... and {len(emails) - 5} more emails")
        
        # Test fetching emails from last 30 days
        print("\n3. Fetching job description emails (last 30 days)...")
        emails_30 = collector.fetch_jd_emails(days_back=30)
        print(f"✅ Found {len(emails_30)} potential job description emails in last 30 days")
        
        # Test email details fetching
        if emails:
            print("\n4. Testing email details fetching...")
            first_email = emails[0]
            email_id = first_email.get('id')
            
            if email_id:
                print(f"   Fetching details for email: {email_id}")
                details = collector._fetch_email_details(email_id)
                
                if details:
                    print("✅ Email details fetched successfully")
                    print(f"   Subject: {details.get('subject', 'No subject')}")
                    print(f"   From: {details.get('from', 'Unknown')}")
                    print(f"   Body length: {len(details.get('body', ''))} characters")
                else:
                    print("❌ Failed to fetch email details")
        
        print("\n🎉 Email collector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email collector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_search_query():
    """Test the email search query configuration."""
    
    print("\n🔍 Testing Email Search Query")
    print("=" * 30)
    
    try:
        config = Config()
        search_query = config.EMAIL_SEARCH_QUERY
        print(f"Current search query: {search_query}")
        
        # Test with different search queries
        test_queries = [
            "subject:(job description OR job posting OR hiring)",
            "subject:(position OR role OR opportunity)",
            "has:attachment"
        ]
        
        print("\nSuggested search queries:")
        for i, query in enumerate(test_queries, 1):
            print(f"   {i}. {query}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search query test failed: {e}")
        return False

if __name__ == "__main__":
    print("JD Agent - Email Collector Test")
    print("=" * 50)
    
    success1 = test_email_collector()
    success2 = test_email_search_query()
    
    if success1 and success2:
        print("\n✅ All email collector tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 