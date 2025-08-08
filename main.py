#!/usr/bin/env python3
"""
Main entry point for JD Agent - Interview Question Harvester

Usage:
    python main.py                    # Run the full pipeline
    python main.py --test            # Run tests
    python main.py --help            # Show help
"""

import sys
import argparse
from jd_agent.main import JDAgent
from jd_agent.utils import get_logger

logger = get_logger(__name__)


async def main():
    """Main entry point for the JD Agent."""
    parser = argparse.ArgumentParser(
        description="JD Agent - Interview Question Harvester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Run the full pipeline
    python main.py --interactive     # Run with email selection interface
    python main.py --days 7          # Process emails from last 7 days
    python main.py --test            # Run tests
    python main.py --validate        # Validate configuration only
        """
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=30,
        help='Number of days back to search for emails (default: 30)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run the test suite'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration only'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode with email selection'
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
        return
    
    if args.validate:
        validate_configuration()
        return
    
    try:
        # Load configuration
        from jd_agent.utils.config import Config
        config = Config.from_env()
        
        # Run the JD Agent
        agent = JDAgent(config)
        
        if args.interactive:
            # Run in interactive mode
            results = await agent.process_emails_interactively(max_emails=20)
        else:
            # Run the full pipeline
            results = await agent.run_full_pipeline(max_emails=10)
        
        # Print results
        print_results(results)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


def run_tests():
    """Run the test suite."""
    import pytest
    import os
    
    print("Running JD Agent test suite...")
    
    # Get the directory containing the tests
    test_dir = os.path.join(os.path.dirname(__file__), 'jd_agent', 'tests')
    
    # Run pytest
    exit_code = pytest.main([
        test_dir,
        '-v',
        '--tb=short'
    ])
    
    if exit_code == 0:
        print("All tests passed!")
    else:
        print("Some tests failed.")
        sys.exit(exit_code)


def validate_configuration():
    """Validate the configuration."""
    from jd_agent.utils.config import Config
    
    print("Validating JD Agent configuration...")
    
    config = Config.from_env()
    try:
        config.validate_required()
        print("✅ Configuration is valid!")
        print("\nConfiguration Summary:")
        print(f"  - Database: {config.DATABASE_PATH}")
        print(f"  - Export Directory: {config.get_export_dir()}")
        print(f"  - OpenAI Model: {config.OPENAI_MODEL}")
        
        # Check API keys (without revealing them)
        print("\nAPI Keys Status:")
        print(f"  - Gmail API: {'✅ Configured' if config.GMAIL_REFRESH_TOKEN else '❌ Missing'}")
        print(f"  - SerpAPI: {'✅ Configured' if config.SERPAPI_KEY else '❌ Missing'}")
        print(f"  - OpenAI: {'✅ Configured' if config.OPENAI_API_KEY else '❌ Missing'}")
        
    except ValueError as e:
        print(f"❌ Configuration is invalid: {e}")
        print("Please check your .env file and ensure all required fields are set.")
        sys.exit(1)


def print_results(results):
    """Print the results in a formatted way."""
    print("\n" + "="*60)
    print("🎯 JD AGENT RESULTS")
    print("="*60)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"❓ Total questions generated: {results.get('total_questions', 0)}")
    print(f"⏱️  Duration: {results.get('duration_seconds', 0):.2f} seconds")
    
    if 'questions_by_difficulty' in results:
        print(f"📊 Questions by difficulty: {results['questions_by_difficulty']}")
    
    if 'average_relevance_score' in results:
        print(f"📈 Average relevance score: {results['average_relevance_score']:.2f}")
    
    if 'export_files' in results and results['export_files']:
        print(f"📁 Export files: {len(results['export_files'])}")
        print("\n📂 Generated Files:")
        for file_path in results['export_files']:
            print(f"  - {file_path}")
    
    if 'usage_stats' in results:
        stats = results['usage_stats']
        print(f"\n📊 Usage Statistics:")
        print(f"  - SerpAPI calls: {stats.get('serpapi_calls', 0)}/{stats.get('max_serpapi_calls', 0)}")
        print(f"  - Scraping methods: {', '.join(stats.get('scraping_methods', []))}")
    
    print("="*60)
    
    if results.get('total_questions', 0) > 0:
        print("🎉 Success! Interview questions have been generated and exported.")
    else:
        print("⚠️  No questions were generated. Check the logs for details.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 