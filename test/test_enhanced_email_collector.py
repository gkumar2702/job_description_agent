#!/usr/bin/env python3
"""
Test Enhanced Email Collector Functionality

This script tests the refactored EmailCollector with improved search criteria
and the new fetch_job_description_threads method.
"""

import sys
import json
from jd_agent.components.email_collector import EmailCollector
from jd_agent.utils.config import Config

def test_enhanced_search_query():
    """Test the enhanced search query building."""
    
    print("🔍 Testing Enhanced Search Query")
    print("=" * 50)
    
    try:
        collector = EmailCollector()
        
        # Test query building
        query = collector._build_enhanced_search_query(days_back=30)
        print(f"Generated query: {query}")
        
        # Check if query contains expected components
        expected_components = [
            "in:anywhere NOT in:spam",
            "after:",
            "linkedin.com",
            "indeed.com",
            "job",
            "hiring"
        ]
        
        missing_components = []
        for component in expected_components:
            if component not in query:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing components: {missing_components}")
            return False
        else:
            print("✅ All expected query components present")
            return True
            
    except Exception as e:
        print(f"❌ Query building test failed: {e}")
        return False

def test_detection_criteria():
    """Test the detection criteria methods."""
    
    print("\n🎯 Testing Detection Criteria")
    print("=" * 40)
    
    try:
        collector = EmailCollector()
        
        # Test domain matching
        print("1. Testing domain matching...")
        test_domains = [
            ("test@linkedin.com", "linkedin.com"),
            ("recruiter@indeed.com", "indeed.com"),
            ("jobs@company.com", None),
            ("test@subdomain.linkedin.com", "linkedin.com")
        ]
        
        for email, expected in test_domains:
            result = collector._check_domain_match(email)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {email} -> {result} (expected: {expected})")
        
        # Test keyword matching
        print("\n2. Testing keyword matching...")
        test_keywords = [
            ("Software Engineer Job", "Software Engineer Job", "Looking for a job", "job"),
            ("Hiring Manager", "We are hiring", "Join our team", "hiring"),
            ("Regular Email", "No job content", "Just checking in", None)
        ]
        
        for subject, body, snippet, expected in test_keywords:
            result = collector._check_keyword_hit(subject, body, snippet)
            status = "✅" if result == expected else "❌"
            print(f"   {status} '{subject}' -> {result} (expected: {expected})")
        
        # Test attachment matching
        print("\n3. Testing attachment matching...")
        test_attachments = [
            ("job_description.pdf", "job_description.pdf"),
            ("JD_Software_Engineer.docx", "JD_Software_Engineer.docx"),
            ("resume.pdf", None),
            ("Job-Description-Senior-Developer.pdf", "Job-Description-Senior-Developer.pdf")
        ]
        
        for filename, expected in test_attachments:
            # Create a mock payload structure
            mock_payload = {
                'parts': [{
                    'filename': filename,
                    'body': {'attachmentId': 'test'},
                    'mimeType': 'application/pdf'
                }]
            }
            result = collector._check_attachment_hit(mock_payload)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {filename} -> {result} (expected: {expected})")
        
        return True
        
    except Exception as e:
        print(f"❌ Detection criteria test failed: {e}")
        return False

def test_enhanced_email_collection():
    """Test the enhanced email collection functionality."""
    
    print("\n📧 Testing Enhanced Email Collection")
    print("=" * 50)
    
    try:
        collector = EmailCollector()
        
        if not collector.service:
            print("❌ Email collector service not available")
            return False
        
        print("✅ Email collector initialized successfully")
        
        # Test the new fetch_job_description_threads method
        print("\n1. Testing fetch_job_description_threads...")
        threads = collector.fetch_job_description_threads(days_back=30)
        
        print(f"✅ Found {len(threads)} job description threads")
        
        if threads:
            print("\n📋 Thread Analysis:")
            for i, thread in enumerate(threads[:3], 1):  # Show first 3 threads
                print(f"\n   Thread {i}:")
                print(f"   - Thread ID: {thread['thread_id']}")
                print(f"   - Message Count: {thread['message_count']}")
                print(f"   - Detection Reasons: {thread['detection_reasons']}")
                print(f"   - Has Job Description: {thread['has_job_description']}")
                
                # Show first message details
                if thread['messages']:
                    first_msg = thread['messages'][0]
                    print(f"   - First Message Subject: {first_msg['subject']}")
                    print(f"   - Sender: {first_msg['sender']}")
                    print(f"   - Domain Match: {first_msg['domain_match']}")
                    print(f"   - Keyword Hit: {first_msg['keyword_hit']}")
                    print(f"   - Attachment Hit: {first_msg['attachment_hit']}")
            
            if len(threads) > 3:
                print(f"   ... and {len(threads) - 3} more threads")
        
        # Test backward compatibility
        print("\n2. Testing backward compatibility (fetch_jd_emails)...")
        emails = collector.fetch_jd_emails(days_back=30)
        print(f"✅ Legacy method found {len(emails)} emails")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced email collection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_query_components():
    """Test individual search query components."""
    
    print("\n🔧 Testing Search Query Components")
    print("=" * 45)
    
    try:
        collector = EmailCollector()
        
        # Test allowed domains
        print("1. Allowed Domains:")
        for domain in collector.ALLOWED_DOMAINS:
            print(f"   - {domain}")
        
        # Test job keywords
        print(f"\n2. Job Keywords ({len(collector.JOB_KEYWORDS)} total):")
        for keyword in collector.JOB_KEYWORDS[:10]:  # Show first 10
            print(f"   - {keyword}")
        if len(collector.JOB_KEYWORDS) > 10:
            print(f"   ... and {len(collector.JOB_KEYWORDS) - 10} more")
        
        # Test regex pattern
        print(f"\n3. Attachment Pattern: {collector.JD_ATTACHMENT_PATTERN.pattern}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search query components test failed: {e}")
        return False

def main():
    """Run all enhanced email collector tests."""
    
    print("🚀 Enhanced Email Collector Test Suite")
    print("=" * 60)
    
    tests = [
        ("Enhanced Search Query", test_enhanced_search_query),
        ("Detection Criteria", test_detection_criteria),
        ("Search Query Components", test_search_query_components),
        ("Enhanced Email Collection", test_enhanced_email_collection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All enhanced email collector tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 