#!/usr/bin/env python3
"""
Gmail Authentication Setup Script for JD Agent

This script helps you set up Gmail API authentication on macOS.
It handles the OAuth flow properly and saves the credentials for future use.
"""

import os
import json
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def setup_gmail_auth():
    """Set up Gmail authentication and save credentials."""
    
    print("🔐 Gmail API Authentication Setup")
    print("=" * 50)
    
    # Check if credentials file exists
    creds_path = Path("credentials.json")
    token_path = Path("data/token.json")
    
    if not creds_path.exists():
        print("❌ Credentials file not found!")
        print("\nTo get your credentials file:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Gmail API' and enable it")
        print("4. Create OAuth2 credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
        print("   - Choose 'Desktop application'")
        print("   - Download the JSON file")
        print("5. Save the downloaded file as 'credentials.json' in this directory")
        print()
        return False
    
    # Create data directory if it doesn't exist
    token_path.parent.mkdir(exist_ok=True)
    
    creds = None
    
    # Check if we have a valid token file
    if token_path.exists():
        try:
            with open(token_path, 'r') as token:
                creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
            print("✅ Found existing token file")
        except Exception as e:
            print(f"⚠️  Failed to load existing token: {e}")
            creds = None
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("✅ Refreshed expired credentials")
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            print("🔄 Starting OAuth flow...")
            try:
                # Load credentials from file
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                
                # Create flow with proper redirect URI for macOS
                flow = InstalledAppFlow.from_client_config(
                    creds_data, 
                    SCOPES,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
                
                print("\n🌐 Opening browser for authentication...")
                print("Please complete the authentication in your browser.")
                print("If the browser doesn't open automatically, copy and paste the URL.")
                
                # Run the flow
                try:
                    creds = flow.run_local_server(port=0)
                    print("✅ Authentication successful!")
                except Exception as auth_error:
                    if "access_denied" in str(auth_error) or "verification" in str(auth_error):
                        print("❌ Access denied: OAuth app not verified")
                        print("\n" + "="*60)
                        print("🔧 QUICK FIX: Add yourself as a test user")
                        print("="*60)
                        print("1. Go to https://console.cloud.google.com/")
                        print("2. Navigate to 'APIs & Services' > 'OAuth consent screen'")
                        print("3. In 'Test users' section, click 'Add Users'")
                        print("4. Add your email: kumar.gourav2702@gmail.com")
                        print("5. Click 'Save'")
                        print("6. Run this script again: python setup_gmail_auth.py")
                        print("="*60)
                        return False
                    else:
                        raise auth_error
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return False
    
    # Save the credentials for future use
    try:
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"💾 Credentials saved to {token_path}")
        
        # Also save to .env format for convenience
        env_path = Path(".env")
        if env_path.exists():
            print("📝 Updating .env file with credentials...")
            update_env_file(env_path, creds)
        
        print("\n🎉 Gmail authentication setup complete!")
        print("You can now use the JD Agent with Gmail integration.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save credentials: {e}")
        return False

def update_env_file(env_path, creds):
    """Update .env file with Gmail credentials."""
    try:
        # Read existing .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add Gmail credentials
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('GMAIL_CLIENT_ID='):
                lines[i] = f"GMAIL_CLIENT_ID={creds.client_id}\n"
                updated = True
            elif line.startswith('GMAIL_CLIENT_SECRET='):
                lines[i] = f"GMAIL_CLIENT_SECRET={creds.client_secret}\n"
                updated = True
            elif line.startswith('GMAIL_REFRESH_TOKEN='):
                lines[i] = f"GMAIL_REFRESH_TOKEN={creds.refresh_token}\n"
                updated = True
        
        # Add missing credentials if not found
        if not any(line.startswith('GMAIL_CLIENT_ID=') for line in lines):
            lines.append(f"GMAIL_CLIENT_ID={creds.client_id}\n")
        if not any(line.startswith('GMAIL_CLIENT_SECRET=') for line in lines):
            lines.append(f"GMAIL_CLIENT_SECRET={creds.client_secret}\n")
        if not any(line.startswith('GMAIL_REFRESH_TOKEN=') for line in lines):
            lines.append(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}\n")
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        print("✅ Updated .env file with Gmail credentials")
        
    except Exception as e:
        print(f"⚠️  Failed to update .env file: {e}")

def test_gmail_connection():
    """Test the Gmail connection."""
    print("\n🧪 Testing Gmail connection...")
    
    try:
        from googleapiclient.discovery import build
        
        # Load credentials
        token_path = Path("data/token.json")
        if not token_path.exists():
            print("❌ No token file found. Please run setup first.")
            return False
        
        with open(token_path, 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
        
        # Build service
        service = build('gmail', 'v1', credentials=creds)
        
        # Test connection by getting profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Connected to Gmail as: {profile['emailAddress']}")
        
        # Test search
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        print(f"✅ Successfully accessed Gmail API")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("JD Agent - Gmail Authentication Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_gmail_connection()
    else:
        success = setup_gmail_auth()
        if success:
            test_gmail_connection()
    
    sys.exit(0 if success else 1) 