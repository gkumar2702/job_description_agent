#!/usr/bin/env python3
"""
Setup Runner for JD Agent

This script provides a convenient way to run setup utilities from the organized folder structure.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
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
    """Run setup utilities."""
    print("🔧 JD Agent Setup Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("jd_agent").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Show available setup options
    print("\n📋 Available Setup Options:")
    print("1. Gmail Authentication Setup")
    print("2. Test Gmail Connection")
    print("3. Check Gmail Status")
    print("4. Fix OAuth Access Issues")
    print("5. Service Account Setup")
    print("6. All Setup Steps")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == "1":
        success = run_command("python setup/setup_gmail_auth.py", "Setting up Gmail Authentication")
    elif choice == "2":
        success = run_command("python setup/setup_gmail_auth.py --test", "Testing Gmail Connection")
    elif choice == "3":
        success = run_command("python setup/check_gmail_status.py", "Checking Gmail Status")
    elif choice == "4":
        success = run_command("python setup/fix_oauth_access.py", "Fixing OAuth Access Issues")
    elif choice == "5":
        success = run_command("python setup/setup_service_account.py", "Setting up Service Account")
    elif choice == "6":
        print("\n🔄 Running all setup steps...")
        
        # Run setup steps in order
        status_success = run_command("python setup/check_gmail_status.py", "Checking Gmail Status")
        
        if not status_success:
            print("\n⚠️  Gmail not configured. Running authentication setup...")
            auth_success = run_command("python setup/setup_gmail_auth.py", "Setting up Gmail Authentication")
            if auth_success:
                test_success = run_command("python setup/setup_gmail_auth.py --test", "Testing Gmail Connection")
                success = test_success
            else:
                success = False
        else:
            test_success = run_command("python setup/setup_gmail_auth.py --test", "Testing Gmail Connection")
            success = test_success
    else:
        print("❌ Invalid choice. Please enter a number between 1-6.")
        sys.exit(1)
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 