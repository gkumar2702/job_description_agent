#!/usr/bin/env python3
"""
Service Account Setup Script for JD Agent

This script helps you set up Gmail API access using a Service Account.
This is often easier for personal projects than OAuth.
"""

import os
import json
import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def setup_service_account():
    """Set up Gmail access using Service Account."""
    
    print("🔐 Gmail API Service Account Setup")
    print("=" * 50)
    
    # Check if service account key file exists
    key_path = Path("service-account-key.json")
    
    if not key_path.exists():
        print("❌ Service account key file not found!")
        print("\nTo get your service account key:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Navigate to 'IAM & Admin' > 'Service Accounts'")
        print("3. Click 'Create Service Account'")
        print("4. Name it 'jd-agent-service'")
        print("5. Grant it the 'Gmail API' role")
        print("6. Create and download the JSON key file")
        print("7. Save it as 'service-account-key.json' in this directory")
        print()
        return False
    
    try:
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            str(key_path), scopes=SCOPES
        )
        
        # Build service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Test connection
        print("🧪 Testing service account connection...")
        
        # Note: Service accounts can't access personal Gmail by default
        # You need to enable domain-wide delegation or use a different approach
        print("⚠️  Service accounts require domain-wide delegation for Gmail access")
        print("For personal Gmail, use OAuth instead.")
        print()
        print("To use OAuth (recommended for personal use):")
        print("1. Add yourself as a test user in OAuth consent screen")
        print("2. Run: python setup_gmail_auth.py")
        
        return False
        
    except Exception as e:
        print(f"❌ Service account setup failed: {e}")
        return False

def print_oauth_instructions():
    """Print instructions for OAuth setup."""
    print("\n" + "="*60)
    print("🔐 OAUTH SETUP INSTRUCTIONS (Recommended)")
    print("="*60)
    print("For personal Gmail access, use OAuth with test users:")
    print()
    print("1. Go to Google Cloud Console > OAuth consent screen")
    print("2. Set User Type to 'External'")
    print("3. Add your email as a test user:")
    print("   - Click 'Add Users' in Test users section")
    print("   - Add: kumar.gourav2702@gmail.com")
    print("4. Save the changes")
    print("5. Run: python setup_gmail_auth.py")
    print()
    print("This will allow you to access your personal Gmail.")
    print("="*60)

if __name__ == "__main__":
    print("JD Agent - Service Account Setup")
    print("=" * 50)
    
    success = setup_service_account()
    if not success:
        print_oauth_instructions()
    
    sys.exit(0 if success else 1) 