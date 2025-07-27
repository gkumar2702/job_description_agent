#!/usr/bin/env python3
"""
Quick Fix for OAuth Access Denied Error

This script provides immediate guidance when you encounter the
"Access blocked: jd_agent has not completed the Google verification process" error.
"""

import webbrowser
import sys

def main():
    print("🔧 OAuth Access Denied - Quick Fix")
    print("=" * 50)
    print()
    print("You're seeing this error because the OAuth app needs test user access.")
    print("Here's how to fix it:")
    print()
    
    # Ask user if they want to open the console
    response = input("Open Google Cloud Console to add yourself as a test user? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        print("Opening Google Cloud Console...")
        webbrowser.open("https://console.cloud.google.com/apis/credentials/consent")
        print()
        print("Once the page opens:")
        print("1. Click 'Add Users' in the 'Test users' section")
        print("2. Add your email: kumar.gourav2702@gmail.com")
        print("3. Click 'Save'")
        print("4. Come back and run: python setup_gmail_auth.py")
    else:
        print()
        print("Manual steps:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials/consent")
        print("2. Click 'Add Users' in the 'Test users' section")
        print("3. Add your email: kumar.gourav2702@gmail.com")
        print("4. Click 'Save'")
        print("5. Run: python setup_gmail_auth.py")
    
    print()
    print("✅ After adding yourself as a test user, the OAuth flow will work!")
    print()

if __name__ == "__main__":
    main() 