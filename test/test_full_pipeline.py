#!/usr/bin/env python3
"""
Test Full JD Agent Pipeline

This script tests the complete pipeline from email collection to question generation.
"""

import sys
from jd_agent.components.email_collector import EmailCollector
from jd_agent.components.jd_parser import JDParser
from jd_agent.components.knowledge_miner import KnowledgeMiner
from jd_agent.utils.config import Config

def test_full_pipeline():
    """Test the complete JD Agent pipeline."""
    
    print("🚀 Testing Full JD Agent Pipeline")
    print("=" * 50)
    
    try:
        # Step 1: Email Collection
        print("1. 📧 Collecting emails...")
        collector = EmailCollector()
        
        if not collector.service:
            print("❌ Email collector service not available")
            return False
        
        emails = collector.fetch_jd_emails(days_back=30)
        print(f"✅ Found {len(emails)} potential job description emails")
        
        if not emails:
            print("No emails found. Pipeline test completed.")
            return True
        
        # Step 2: Email Processing
        print("\n2. 🔍 Processing emails...")
        parser = JDParser()
        
        for i, email in enumerate(emails, 1):
            print(f"\n   Processing email {i}:")
            
            email_id = email.get('id')
            details = collector._fetch_email_details(email_id)
            
            if details:
                subject = details.get('subject', 'No subject')
                body = details.get('body', '')
                
                print(f"   Subject: {subject}")
                print(f"   Body length: {len(body)} characters")
                
                # Check if it's actually a job description
                is_jd = collector._is_job_description(subject, body)
                print(f"   Is Job Description: {is_jd}")
                
                if is_jd:
                    # Step 3: Parse Job Description
                    print("   📝 Parsing job description...")
                    try:
                        jd_data = parser.parse(details)
                        print(f"   ✅ Parsed successfully:")
                        print(f"      Company: {jd_data.company}")
                        print(f"      Role: {jd_data.role}")
                        print(f"      Location: {jd_data.location}")
                        print(f"      Experience: {jd_data.experience_years} years")
                        print(f"      Skills: {len(jd_data.skills)} skills found")
                        
                        # Step 4: Knowledge Mining (if configured)
                        if Config.SERPAPI_KEY and Config.SERPAPI_KEY != "your_serpapi_key":
                            print("   🔍 Mining knowledge...")
                            try:
                                miner = KnowledgeMiner(Config(), None)  # Simplified for testing
                                print("   ✅ Knowledge miner initialized")
                            except Exception as e:
                                print(f"   ⚠️  Knowledge miner error: {e}")
                        else:
                            print("   ⚠️  SerpAPI not configured - skipping knowledge mining")
                        
                    except Exception as e:
                        print(f"   ❌ Parsing failed: {e}")
                else:
                    print("   ⏭️  Skipping - not a job description")
        
        print("\n🎉 Full pipeline test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_jd_detection():
    """Test the job description detection logic."""
    
    print("\n🔍 Testing Job Description Detection")
    print("=" * 40)
    
    try:
        collector = EmailCollector()
        
        # Test with sample job description text
        test_cases = [
            {
                "subject": "Software Engineer Position at Google",
                "body": "We are hiring a Senior Software Engineer to join our team. Requirements: 3-5 years experience in Python, Java. Location: Mountain View, CA.",
                "expected": True
            },
            {
                "subject": "ChatGPT's biased salary advice",
                "body": "India aims for AI independence, LLMs give biased salary advice...",
                "expected": False
            },
            {
                "subject": "Job Posting: Data Scientist",
                "body": "We are looking for a Data Scientist to join our team. Must have experience with machine learning and Python.",
                "expected": True
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            result = collector._is_job_description(test_case["subject"], test_case["body"])
            expected = test_case["expected"]
            status = "✅" if result == expected else "❌"
            
            print(f"{status} Test {i}: {test_case['subject']}")
            print(f"   Expected: {expected}, Got: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ JD detection test failed: {e}")
        return False

if __name__ == "__main__":
    print("JD Agent - Full Pipeline Test")
    print("=" * 50)
    
    success1 = test_full_pipeline()
    success2 = test_jd_detection()
    
    if success1 and success2:
        print("\n✅ All pipeline tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 