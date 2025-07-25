"""
Example usage of the JD Agent system.

Demonstrates how to use the JD Agent to process job descriptions
and generate interview questions using the new LangGraph-based scraping agent.
"""

import asyncio
import os
from datetime import datetime

from jd_agent.utils.config import Config
from jd_agent.utils.logger import setup_logger
from jd_agent.main import JDAgent

# Setup logging
setup_logger()
logger = setup_logger(__name__)


async def main():
    """Main example function."""
    print("🚀 JD Agent Examples")
    print("=" * 50)
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found. Some examples may fail.")
        print("   Please create a .env file with your API keys.")
        print("   See .env.example for reference.\n")
    
    # Load configuration
    config = Config()
    
    # Validate configuration
    print("=== Example: Configuration Validation ===")
    print("Validating configuration...")
    
    if not config.validate():
        print("❌ Configuration is invalid!")
        print("Please check your .env file.")
        return
    
    print("✅ Configuration is valid!")
    
    # Initialize JD Agent
    try:
        agent = JDAgent(config)
        print("✅ JD Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize JD Agent: {e}")
        return
    
    # Example 1: Process a single job description
    print("\n=== Example: Single Job Description Processing ===")
    
    sample_jd = """
    Senior Data Scientist
    
    Company: TechCorp
    Location: San Francisco, CA
    Experience: 5+ years
    
    We are looking for a Senior Data Scientist to join our team. You will be responsible for:
    - Developing machine learning models for predictive analytics
    - Working with large datasets using Python, SQL, and PySpark
    - Collaborating with cross-functional teams
    - Implementing statistical analysis and A/B testing
    
    Requirements:
    - Strong Python programming skills
    - Experience with machine learning frameworks (scikit-learn, TensorFlow, PyTorch)
    - Proficiency in SQL and data manipulation
    - Knowledge of statistical analysis and experimental design
    - Experience with big data technologies (Hadoop, Spark)
    - Excellent communication skills
    
    Nice to have:
    - Experience with deep learning
    - Knowledge of cloud platforms (AWS, GCP)
    - Experience with MLOps and model deployment
    """
    
    try:
        questions = await agent.process_single_jd(sample_jd, "TechCorp")
        print(f"✅ Generated {len(questions)} questions")
        
        if questions:
            print("\nSample questions:")
            for i, q in enumerate(questions[:3], 1):
                print(f"{i}. {q.get('question', 'No question text')}")
                print(f"   Difficulty: {q.get('difficulty', 'Unknown')}")
                print(f"   Category: {q.get('category', 'Unknown')}")
                print()
        
    except Exception as e:
        print(f"❌ Error processing job description: {e}")
    
    # Example 2: Custom search with specific sources
    print("\n=== Example: Custom Search with Free Scraping ===")
    
    custom_jd = """
    Data Scientist
    
    Company: Example Corp
    Location: Remote
    Experience: 2-4 years
    
    Skills: Python, SQL, Machine Learning, Statistics, Data Analysis
    """
    
    try:
        # This will use the LangGraph-based scraping agent
        questions = await agent.process_single_jd(custom_jd, "Example Corp")
        print(f"✅ Generated {len(questions)} questions using free scraping methods")
        
        # Show usage statistics
        usage_stats = agent.scraping_agent.get_usage_stats()
        print(f"📊 Scraping Statistics:")
        print(f"   SerpAPI calls: {usage_stats['serpapi_calls']}/{usage_stats['max_serpapi_calls']}")
        print(f"   Scraping methods used: {', '.join(usage_stats['scraping_methods'])}")
        print(f"   Rate limiting: {usage_stats['rate_limiting']}")
        
    except Exception as e:
        print(f"❌ Error in custom search: {e}")
    
    # Example 3: Full pipeline (if emails are available)
    print("\n=== Example: Full Pipeline ===")
    print("Note: This requires Gmail API setup and job description emails.")
    print("Skipping for demo purposes.")
    
    print("\n" + "=" * 50)
    print("✅ Examples completed!")
    print("\nTo run the full pipeline with real data:")
    print("1. Set up your .env file with API keys")
    print("2. Run: python main.py")
    print("3. Or run: python main.py --validate")


if __name__ == "__main__":
    asyncio.run(main()) 