#!/usr/bin/env python3
"""
Test Runner for JD Agent

This script provides a convenient way to run all tests from the organized folder structure.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    print()
    
    try:
        # Set PYTHONPATH to include current directory
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd() + ':' + env.get('PYTHONPATH', '')
        
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, env=env)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Run all tests."""
    print("🚀 JD Agent Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("jd_agent").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Run unit tests
    print("\n📋 Available Tests:")
    print("1. Unit Tests (pytest)")
    print("2. Basic Functionality Test")
    print("3. Email Collector Test")
    print("4. Email Analysis Test")
    print("5. Full Pipeline Test")
    print("6. Enhanced Email Collector Test")
    print("7. Enhanced JDParser Test")
    print("8. Pipeline Results Check")
    print("9. All Tests")
    
    choice = input("\nEnter your choice (1-9): ").strip()
    
    if choice == "1":
        success = run_command("pytest jd_agent/tests/ -v", "Running Unit Tests")
    elif choice == "2":
        success = run_command("python test/test_demo.py", "Running Basic Functionality Test")
    elif choice == "3":
        success = run_command("python test/test_email_collector.py", "Running Email Collector Test")
    elif choice == "4":
        success = run_command("python test/test_email_details.py", "Running Email Analysis Test")
    elif choice == "5":
        success = run_command("python test/test_full_pipeline.py", "Running Full Pipeline Test")
    elif choice == "6":
        success = run_command("python test/test_enhanced_email_collector.py", "Running Enhanced Email Collector Test")
    elif choice == "7":
        success = run_command("python test/test_enhanced_jd_parser.py", "Running Enhanced JDParser Test")
    elif choice == "8":
        success = run_command("python test/check_pipeline_results.py", "Running Pipeline Results Check")
    elif choice == "9":
        print("\n🔄 Running all tests...")
        
        # Run unit tests
        unit_success = run_command("pytest jd_agent/tests/ -v", "Running Unit Tests")
        
        # Run functional tests
        func_success = run_command("python test/test_demo.py", "Running Basic Functionality Test")
        email_success = run_command("python test/test_email_collector.py", "Running Email Collector Test")
        analysis_success = run_command("python test/test_email_details.py", "Running Email Analysis Test")
        pipeline_success = run_command("python test/test_full_pipeline.py", "Running Full Pipeline Test")
        enhanced_email_success = run_command("python test/test_enhanced_email_collector.py", "Running Enhanced Email Collector Test")
        enhanced_parser_success = run_command("python test/test_enhanced_jd_parser.py", "Running Enhanced JDParser Test")
        pipeline_check_success = run_command("python test/check_pipeline_results.py", "Running Pipeline Results Check")
        
        success = (unit_success and func_success and email_success and analysis_success and 
                  pipeline_success and enhanced_email_success and enhanced_parser_success and pipeline_check_success)
    else:
        print("❌ Invalid choice. Please enter a number between 1-9.")
        sys.exit(1)
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 