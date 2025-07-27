#!/usr/bin/env python3
"""
Test Gmail Authentication Status

This script checks the current status of Gmail authentication
and provides guidance on what needs to be done.
"""

import os
import json
from pathlib import Path

def check_gmail_status():
    """Check the current Gmail authentication status."""
    
    print("🔍 Gmail Authentication Status Check")
    print("=" * 50)
    
    # Check for credentials file
    creds_path = Path("credentials.json")
    if creds_path.exists():
        print("✅ Credentials file found: credentials.json")
    else:
        print("❌ Credentials file missing: credentials.json")
        print("   Download OAuth credentials from Google Cloud Console")
    
    # Check for token file
    token_path = Path("data/token.json")
    if token_path.exists():
        print("✅ Token file found: data/token.json")
        try:
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            print(f"   Token expires: {token_data.get('expiry', 'Unknown')}")
        except Exception as e:
            print(f"   ⚠️  Error reading token: {e}")
    else:
        print("❌ Token file missing: data/token.json")
        print("   Run: python setup/setup_gmail_auth.py")
    
    # Check for .env file
    env_path = Path(".env")
    if env_path.exists():
        print("✅ Environment file found: .env")
        with open(env_path, 'r') as f:
            env_content = f.read()
        if "GMAIL_CLIENT_ID" in env_content:
            print("   ✅ Gmail credentials in .env")
        else:
            print("   ❌ Gmail credentials missing from .env")
    else:
        print("❌ Environment file missing: .env")
    
    print()
    print("📋 Next Steps:")
    if not creds_path.exists():
        print("1. Download OAuth credentials from Google Cloud Console")
        print("2. Save as 'credentials.json' in project root")
    elif not token_path.exists():
        print("1. Add yourself as test user in OAuth consent screen")
        print("2. Run: python setup/setup_gmail_auth.py")
    else:
        print("1. Test connection: python setup/setup_gmail_auth.py --test")
    
    print()
    print("🔗 Useful Links:")
    print("- Google Cloud Console: https://console.cloud.google.com/")
    print("- OAuth Consent Screen: https://console.cloud.google.com/apis/credentials/consent")

if __name__ == "__main__":
    check_gmail_status() 