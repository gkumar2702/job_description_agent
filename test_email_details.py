#!/usr/bin/env python3
"""
Detailed Email Analysis Test

This script provides detailed analysis of the emails found by the collector.
"""

import sys
from jd_agent.components.email_collector import EmailCollector
from jd_agent.utils.config import Config

def analyze_emails():
    """Analyze the emails found by the collector."""
    
    print("📧 Detailed Email Analysis")
    print("=" * 50)
    
    try:
        # Initialize the email collector
        collector = EmailCollector()
        
        if not collector.service:
            print("❌ Email collector service not available")
            return False
        
        # Fetch emails from last 30 days
        print("Fetching emails from last 30 days...")
        emails = collector.fetch_jd_emails(days_back=30)
        
        print(f"Found {len(emails)} potential job description emails")
        
        if not emails:
            print("No emails found. This could mean:")
            print("1. No job description emails in the last 30 days")
            print("2. Search query needs adjustment")
            print("3. Emails are in different labels/folders")
            return True
        
        # Analyze each email
        for i, email in enumerate(emails, 1):
            print(f"\n📧 Email {i}:")
            print("-" * 30)
            
            email_id = email.get('id')
            print(f"ID: {email_id}")
            
            # Get detailed email information
            details = collector._fetch_email_details(email_id)
            
            if details:
                subject = details.get('subject', 'No subject')
                sender = details.get('from', 'Unknown sender')
                date = details.get('date', 'Unknown date')
                body = details.get('body', '')
                
                print(f"Subject: {subject}")
                print(f"From: {sender}")
                print(f"Date: {date}")
                print(f"Body length: {len(body)} characters")
                
                # Check if it's actually a job description
                is_jd = collector._is_job_description(subject, body)
                print(f"Is Job Description: {is_jd}")
                
                # Show first 200 characters of body
                if body:
                    preview = body[:200].replace('\n', ' ').strip()
                    print(f"Preview: {preview}...")
                
                # Check for attachments
                attachments = collector.get_email_attachments(email_id)
                if attachments:
                    print(f"Attachments: {len(attachments)} found")
                    for att in attachments:
                        print(f"  - {att.get('filename', 'Unknown')} ({att.get('size', 0)} bytes)")
                else:
                    print("Attachments: None")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Email analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_queries():
    """Test different search queries to find more emails."""
    
    print("\n🔍 Testing Different Search Queries")
    print("=" * 40)
    
    try:
        collector = EmailCollector()
        
        # Test different search queries
        test_queries = [
            "subject:(job description OR job posting OR hiring)",
            "subject:(position OR role OR opportunity)",
            "has:attachment",
            "label:inbox",
            "from:linkedin.com",
            "from:indeed.com",
            "from:glassdoor.com"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: {query}")
            try:
                # Temporarily modify the search query
                original_query = Config.EMAIL_SEARCH_QUERY
                Config.EMAIL_SEARCH_QUERY = query
                
                emails = collector.fetch_jd_emails(days_back=30)
                print(f"  Found: {len(emails)} emails")
                
                # Restore original query
                Config.EMAIL_SEARCH_QUERY = original_query
                
            except Exception as e:
                print(f"  Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search query test failed: {e}")
        return False

if __name__ == "__main__":
    print("JD Agent - Detailed Email Analysis")
    print("=" * 50)
    
    success1 = analyze_emails()
    success2 = test_search_queries()
    
    if success1 and success2:
        print("\n✅ Email analysis completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 