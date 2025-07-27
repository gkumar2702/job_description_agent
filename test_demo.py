#!/usr/bin/env python3
"""
Simple demo script to test JD Agent functionality
"""

import os
import sys
from jd_agent.components.jd_parser import JDParser
from jd_agent.utils.config import Config

def test_basic_functionality():
    """Test basic functionality without requiring API keys."""
    print("🧪 Testing JD Agent Basic Functionality")
    print("=" * 50)
    
    # Test 1: Configuration
    print("1. Testing configuration...")
    try:
        config = Config()
        print("   ✅ Configuration loaded successfully")
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        return False
    
    # Test 2: JDParser
    print("2. Testing JDParser...")
    try:
        parser = JDParser()
        print("   ✅ JDParser initialized successfully")
        
        # Test parsing a sample job description
        sample_jd = {
            'subject': 'Software Engineer Position at Google',
            'body': '''
            We are looking for a Senior Software Engineer to join our team at Google.
            
            Requirements:
            - 3-5 years of experience in Python, Java, or C++
            - Experience with machine learning and data analysis
            - Strong problem-solving skills
            - Bachelor's degree in Computer Science or related field
            
            Location: Mountain View, CA
            '''
        }
        
        result = parser.parse(sample_jd)
        print(f"   ✅ Parsed JD successfully: {result.role} at {result.company}")
        
    except Exception as e:
        print(f"   ❌ JDParser test failed: {e}")
        return False
    
    # Test 3: Package imports
    print("3. Testing package imports...")
    try:
        from jd_agent.components import EmailCollector, KnowledgeMiner
        from jd_agent.utils import database, logger
        print("   ✅ All components import successfully")
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False
    
    print("\n🎉 All basic functionality tests passed!")
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1) 