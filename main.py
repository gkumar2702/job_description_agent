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
from jd_agent.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Main entry point for the JD Agent."""
    parser = argparse.ArgumentParser(
        description="JD Agent - Interview Question Harvester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Run the full pipeline
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
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
        return
    
    if args.validate:
        validate_configuration()
        return
    
    try:
        # Run the JD Agent
        agent = JDAgent()
        results = agent.run(days_back=args.days)
        
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
    from jd_agent.utils import Config
    
    print("Validating JD Agent configuration...")
    
    if Config.validate():
        print("✅ Configuration is valid!")
        print("\nConfiguration Summary:")
        print(f"  - Database: {Config.DATABASE_PATH}")
        print(f"  - Export Directory: {Config.get_export_dir()}")
        print(f"  - Max Search Results: {Config.MAX_SEARCH_RESULTS}")
        print(f"  - OpenAI Model: {Config.OPENAI_MODEL}")
        print(f"  - Log Level: {Config.LOG_LEVEL}")
        
        # Check API keys (without revealing them)
        print("\nAPI Keys Status:")
        print(f"  - Gmail API: {'✅ Configured' if Config.GMAIL_CLIENT_ID else '❌ Missing'}")
        print(f"  - SerpAPI: {'✅ Configured' if Config.SERPAPI_KEY else '❌ Missing'}")
        print(f"  - OpenAI: {'✅ Configured' if Config.OPENAI_API_KEY else '❌ Missing'}")
        
    else:
        print("❌ Configuration is invalid!")
        print("Please check your .env file and ensure all required fields are set.")
        sys.exit(1)


def print_results(results):
    """Print the results in a formatted way."""
    print("\n" + "="*60)
    print("🎯 JD AGENT RESULTS")
    print("="*60)
    
    print(f"📧 Emails processed: {results['emails_processed']}")
    print(f"📋 Job descriptions parsed: {results['job_descriptions_parsed']}")
    print(f"❓ Questions generated: {results['questions_generated']}")
    print(f"📁 Export files: {len(results['export_files'])}")
    
    if results['export_files']:
        print("\n📂 Generated Files:")
        for format_type, file_path in results['export_files'].items():
            print(f"  - {format_type.upper()}: {file_path}")
    
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("="*60)
    
    if results['questions_generated'] > 0:
        print("🎉 Success! Interview questions have been generated and exported.")
    else:
        print("⚠️  No questions were generated. Check the logs for details.")


if __name__ == "__main__":
    main() 