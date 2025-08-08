#!/usr/bin/env python3
"""
Quick test to verify enhanced JD parser works with real email patterns.
"""

import sys
import os

# Add the parent directory to the path to import jd_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jd_agent.components.jd_parser import JDParser, JobDescription

def test_enhanced_jd_parser():
    """Test the enhanced JD parser with real email patterns."""
    parser = JDParser()
    
    # Test with AI Engineer email pattern
    ai_engineer_text = """
    UST (www.ust.com) is looking for AI Engineer for Bangalore Location.(Manyata Tech Park)
    Exp - 5+ Years
    
    We are currently looking to onboard an experienced AI Engineer to support our AI initiatives.
    Key Requirements:
    * Overall 5+ yrs experience with 2+ years of hands-on experience in developing AI/ML applications
    * Proficiency in Python and frameworks such as TensorFlow, PyTorch, Hugging Face, or Scikit-learn
    * Strong understanding of machine learning pipelines and deployment
    * Experience with cloud AI/ML platforms
    * Familiarity with workflow tools like Airflow, Kubeflow, or LangChain
    """
    
    email_data = {
        'subject': 'AI Engineer ll Bangalore (Manyata Tech Park)',
        'body': ai_engineer_text,
        'from': 'careers@ust.com',
        'id': 'test_ai_engineer'
    }
    
    result = parser.parse(email_data)
    
    if result:
        print("✅ AI Engineer parsing successful!")
        print(f"Company: {result.company}")
        print(f"Role: {result.role}")
        print(f"Location: {result.location}")
        print(f"Experience: {result.experience_years} years")
        print(f"Skills: {result.skills[:5]}")  # First 5 skills
        print(f"Confidence: {result.confidence_score:.2f}")
        print()
    else:
        print("❌ AI Engineer parsing failed!")
    
    # Test with Lead Data Scientist email pattern
    data_scientist_text = """
    I'm hiring for an Lead Data Scientist at Acuity Knowledge Partners.
    (Bangalore • hybrid 2 days on-site • salary up to ₹ 50 LPA).
    If you have 7–9 years in data-science/ML research and enjoy leading high-impact projects.
    
    Key responsibilities:
    * Build, fine-tune and deploy ML / LLM / NLP models
    * Select features & optimise classifiers; run data-mining experiments
    * Cleanse, verify and enrich large, multi-source datasets
    * Design data-collection pipelines for new analytics use-cases
    """
    
    email_data2 = {
        'subject': 'Job Opportunity - Lead Data Scientist | ₹ 50 LPA (max) | Bangalore (2‑day Hybrid)',
        'body': data_scientist_text,
        'from': 'rashi.singh@lorienglobal.com',
        'id': 'test_data_scientist'
    }
    
    result2 = parser.parse(email_data2)
    
    if result2:
        print("✅ Lead Data Scientist parsing successful!")
        print(f"Company: {result2.company}")
        print(f"Role: {result2.role}")
        print(f"Location: {result2.location}")
        print(f"Experience: {result2.experience_years} years")
        print(f"Salary: {result2.salary_lpa} LPA")
        print(f"Skills: {result2.skills[:5]}")  # First 5 skills
        print(f"Confidence: {result2.confidence_score:.2f}")
        print()
    else:
        print("❌ Lead Data Scientist parsing failed!")
    
    # Test with simple job description
    simple_text = "Software Engineer at TechCorp"
    result3 = parser.parse_job_description(simple_text, "TechCorp")
    
    if result3:
        print("✅ Simple parsing successful!")
        print(f"Company: {result3.company}")
        print(f"Role: {result3.role}")
        print(f"Location: {result3.location}")
        print(f"Confidence: {result3.confidence_score:.2f}")
    else:
        print("❌ Simple parsing failed!")

if __name__ == '__main__':
    test_enhanced_jd_parser()