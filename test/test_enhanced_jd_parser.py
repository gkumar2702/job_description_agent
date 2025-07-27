#!/usr/bin/env python3
"""
Test Enhanced JDParser

This script tests the enhanced JDParser to verify improvements in parsing accuracy.
"""

import json
import sys
from jd_agent.components.jd_parser import JDParser
from jd_agent.components.email_collector import EmailCollector

def test_enhanced_parser():
    """Test the enhanced JDParser with real email data."""
    print("🧪 Testing Enhanced JDParser")
    print("=" * 60)
    
    # Initialize parser
    parser = JDParser()
    print("✅ Enhanced JDParser initialized")
    
    # Load test data from previous run
    try:
        with open('data/parsed_jds.json', 'r') as f:
            old_results = json.load(f)
        print(f"📊 Loaded {len(old_results)} previous parsing results")
    except FileNotFoundError:
        print("❌ No previous results found. Run pipeline first.")
        return
    
    # Get fresh email data
    try:
        collector = EmailCollector()
        emails = collector.fetch_jd_emails(days_back=7)
        print(f"📧 Loaded {len(emails)} fresh emails")
    except Exception as e:
        print(f"❌ Failed to load emails: {e}")
        return
    
    # Test enhanced parsing
    print("\n🔍 Testing Enhanced Parsing...")
    print("=" * 50)
    
    enhanced_results = []
    improvements = []
    
    for i, email in enumerate(emails[:5], 1):
        print(f"\n📝 Parsing email {i}:")
        print(f"   Subject: {email.get('subject', 'No subject')[:50]}...")
        print(f"   Sender: {email.get('from', 'No sender')}")
        
        # Parse with enhanced parser
        jd = parser.parse(email)
        
        if jd:
            enhanced_results.append({
                'email_id': email.get('id', ''),
                'subject': email.get('subject', ''),
                'sender': email.get('from', ''),
                'parsed_data': {
                    'company': jd.company,
                    'role': jd.role,
                    'location': jd.location,
                    'experience_years': jd.experience_years,
                    'skills': jd.skills,
                    'content_length': len(jd.content),
                    'confidence_score': jd.confidence_score,
                    'parsing_metadata': jd.parsing_metadata
                }
            })
            
            print(f"   ✅ Enhanced parsing successful:")
            print(f"      Company: {jd.company}")
            print(f"      Role: {jd.role}")
            print(f"      Location: {jd.location}")
            print(f"      Experience: {jd.experience_years} years")
            print(f"      Skills: {len(jd.skills)} skills")
            print(f"      Confidence: {jd.confidence_score:.2f}")
            
            # Compare with old results
            old_result = next((r for r in old_results if r['email_id'] == email.get('id', '')), None)
            if old_result:
                print(f"   📊 Comparison with old parser:")
                print(f"      Old Company: {old_result['parsed_data']['company']}")
                print(f"      New Company: {jd.company}")
                print(f"      Old Role: {old_result['parsed_data']['role']}")
                print(f"      New Role: {jd.role}")
                
                # Check for improvements
                if jd.company != old_result['parsed_data']['company']:
                    improvements.append(f"Company: {old_result['parsed_data']['company']} → {jd.company}")
                if jd.role != old_result['parsed_data']['role']:
                    improvements.append(f"Role: {old_result['parsed_data']['role']} → {jd.role}")
                if jd.confidence_score > 0.5:
                    improvements.append(f"High confidence: {jd.confidence_score:.2f}")
        else:
            print(f"   ❌ Failed to parse")
    
    # Save enhanced results
    with open('data/enhanced_parsed_jds.json', 'w') as f:
        json.dump(enhanced_results, f, indent=2, default=str)
    
    print(f"\n📁 Enhanced results saved to: data/enhanced_parsed_jds.json")
    
    # Show improvements
    if improvements:
        print(f"\n🎉 Improvements Found:")
        print("=" * 30)
        for improvement in improvements:
            print(f"   ✅ {improvement}")
    else:
        print(f"\n📊 No significant improvements detected")
    
    # Show confidence statistics
    confidence_scores = [r['parsed_data']['confidence_score'] for r in enhanced_results if r['parsed_data']['confidence_score'] > 0]
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        print(f"\n📈 Confidence Statistics:")
        print(f"   Average confidence: {avg_confidence:.2f}")
        print(f"   High confidence (>0.7): {sum(1 for c in confidence_scores if c > 0.7)}/{len(confidence_scores)}")
        print(f"   Medium confidence (0.4-0.7): {sum(1 for c in confidence_scores if 0.4 <= c <= 0.7)}/{len(confidence_scores)}")
        print(f"   Low confidence (<0.4): {sum(1 for c in confidence_scores if c < 0.4)}/{len(confidence_scores)}")

def test_company_extraction():
    """Test company extraction specifically."""
    print("\n🏢 Testing Company Extraction")
    print("=" * 50)
    
    parser = JDParser()
    
    test_cases = [
        {
            'subject': 'Software Engineer at Google',
            'sender': 'Google Careers <careers@google.com>',
            'body': 'Join Google as a Software Engineer...',
            'expected_company': 'Google'
        },
        {
            'subject': 'Data Scientist - Microsoft',
            'sender': 'Microsoft Recruiting <recruiting@microsoft.com>',
            'body': 'Microsoft is hiring a Data Scientist...',
            'expected_company': 'Microsoft'
        },
        {
            'subject': 'Product Manager at Amazon',
            'sender': 'Amazon Jobs <jobs@amazon.com>',
            'body': 'Amazon is looking for a Product Manager...',
            'expected_company': 'Amazon'
        },
        {
            'subject': 'LinkedIn Job Alert: Senior Engineer',
            'sender': 'LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>',
            'body': 'New job at Apple: Senior Engineer...',
            'expected_company': 'Apple'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['subject']}")
        
        email_data = {
            'id': f'test_{i}',
            'subject': test_case['subject'],
            'from': test_case['sender'],
            'body': test_case['body']
        }
        
        jd = parser.parse(email_data)
        
        if jd:
            print(f"   Extracted: {jd.company}")
            print(f"   Expected: {test_case['expected_company']}")
            print(f"   Match: {'✅' if jd.company.lower() == test_case['expected_company'].lower() else '❌'}")
            print(f"   Confidence: {jd.confidence_score:.2f}")
            print(f"   Method: {jd.parsing_metadata['extraction_methods']['company']}")
        else:
            print(f"   ❌ Failed to parse")

def test_role_extraction():
    """Test role extraction specifically."""
    print("\n👨‍💼 Testing Role Extraction")
    print("=" * 50)
    
    parser = JDParser()
    
    test_cases = [
        {
            'subject': '"Senior Software Engineer" at Google',
            'body': 'We are looking for a Senior Software Engineer...',
            'expected_role': 'Senior Software Engineer'
        },
        {
            'subject': 'Data Scientist Position',
            'body': 'Join us as a Data Scientist...',
            'expected_role': 'Data Scientist'
        },
        {
            'subject': 'Product Manager Role',
            'body': 'Become a Product Manager at our company...',
            'expected_role': 'Product Manager'
        },
        {
            'subject': 'Machine Learning Engineer',
            'body': 'We need a Machine Learning Engineer...',
            'expected_role': 'Machine Learning Engineer'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['subject']}")
        
        email_data = {
            'id': f'test_{i}',
            'subject': test_case['subject'],
            'from': 'test@company.com',
            'body': test_case['body']
        }
        
        jd = parser.parse(email_data)
        
        if jd:
            print(f"   Extracted: {jd.role}")
            print(f"   Expected: {test_case['expected_role']}")
            print(f"   Match: {'✅' if jd.role.lower() == test_case['expected_role'].lower() else '❌'}")
            print(f"   Confidence: {jd.confidence_score:.2f}")
            print(f"   Method: {jd.parsing_metadata['extraction_methods']['role']}")
        else:
            print(f"   ❌ Failed to parse")

def main():
    """Run all tests."""
    print("🚀 Enhanced JDParser Test Suite")
    print("=" * 60)
    
    # Test enhanced parsing with real data
    test_enhanced_parser()
    
    # Test specific extraction methods
    test_company_extraction()
    test_role_extraction()
    
    print("\n" + "=" * 60)
    print("✅ Enhanced JDParser testing completed!")
    print("\n📊 Key Improvements:")
    print("   • Multi-strategy company extraction")
    print("   • Enhanced role detection patterns")
    print("   • Confidence scoring system")
    print("   • Better skills categorization")
    print("   • Parsing metadata tracking")
    print("   • Improved validation logic")

if __name__ == "__main__":
    main() 