#!/usr/bin/env python3
"""
Run Pipeline and Check Results

This script runs the full JD Agent pipeline and then shows you where all the results are stored.
"""

import os
import sys
import json
import sqlite3
import asyncio
from datetime import datetime
from jd_agent.components.email_collector import EmailCollector
from jd_agent.components.jd_parser import JDParser
from jd_agent.utils.config import Config
from jd_agent.utils.database import Database

def run_email_collection():
    """Run EmailCollector and store results."""
    print("📧 Running EmailCollector...")
    print("=" * 50)
    
    try:
        collector = EmailCollector()
        
        if not collector.service:
            print("❌ EmailCollector service not available")
            return None, None
        
        # Get threads and emails
        threads = collector.fetch_job_description_threads(days_back=7)
        emails = collector.fetch_jd_emails(days_back=7)
        
        print(f"✅ Found {len(threads)} threads and {len(emails)} emails")
        
        # Store thread data in a file for inspection
        thread_file = "data/email_threads.json"
        os.makedirs(os.path.dirname(thread_file), exist_ok=True)
        
        with open(thread_file, 'w') as f:
            json.dump(threads, f, indent=2, default=str)
        
        print(f"📁 Thread data saved to: {thread_file}")
        
        return threads, emails
        
    except Exception as e:
        print(f"❌ EmailCollector failed: {e}")
        return None, None

def run_jd_parsing(emails):
    """Run JDParser and store results."""
    print("\n📝 Running JDParser...")
    print("=" * 50)
    
    if not emails:
        print("❌ No emails to parse")
        return []
    
    try:
        parser = JDParser()
        parsed_jds = []
        
        for i, email in enumerate(emails[:5], 1):  # Parse first 5 emails
            print(f"Parsing email {i}/{min(5, len(emails))}...")
            
            jd = parser.parse(email)
            if jd:
                parsed_jds.append({
                    'email_id': email.get('id', ''),
                    'subject': email.get('subject', ''),
                    'sender': email.get('from', ''),
                    'parsed_data': {
                        'company': jd.company,
                        'role': jd.role,
                        'location': jd.location,
                        'experience_years': jd.experience_years,
                        'skills': jd.skills,
                        'content_length': len(jd.content)
                    }
                })
                print(f"  ✅ Parsed: {jd.company} - {jd.role}")
            else:
                print(f"  ❌ Failed to parse")
        
        # Store parsed data in a file
        parsed_file = "data/parsed_jds.json"
        with open(parsed_file, 'w') as f:
            json.dump(parsed_jds, f, indent=2, default=str)
        
        print(f"📁 Parsed JD data saved to: {parsed_file}")
        print(f"✅ Successfully parsed {len(parsed_jds)} job descriptions")
        
        return parsed_jds
        
    except Exception as e:
        print(f"❌ JDParser failed: {e}")
        return []

def check_database_after_pipeline():
    """Check database after pipeline execution."""
    print("\n🗄️  Checking Database After Pipeline...")
    print("=" * 50)
    
    db_path = Config.DATABASE_PATH
    
    if os.path.exists(db_path):
        print("✅ Database file exists")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables found: {[table[0] for table in tables]}")
            
            # Check each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {table_name}: {count} records")
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                    row = cursor.fetchone()
                    print(f"    Sample: {str(row)[:100]}...")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
    else:
        print("❌ Database file still doesn't exist")
        print("This means the pipeline didn't store results in the database")

def check_all_storage_locations():
    """Check all possible storage locations."""
    print("\n📁 Checking All Storage Locations...")
    print("=" * 50)
    
    storage_locations = [
        ("Database", Config.DATABASE_PATH),
        ("Email Threads", "data/email_threads.json"),
        ("Parsed JDs", "data/parsed_jds.json"),
        ("Exports", Config.get_export_dir()),
        ("Token File", "data/token.json"),
        ("Credentials", "credentials.json")
    ]
    
    for name, path in storage_locations:
        if os.path.exists(path):
            if os.path.isdir(path):
                files = os.listdir(path)
                print(f"✅ {name}: {path} ({len(files)} files)")
            else:
                size = os.path.getsize(path)
                print(f"✅ {name}: {path} ({size} bytes)")
        else:
            print(f"❌ {name}: {path} (not found)")

def show_sample_results():
    """Show sample results from storage."""
    print("\n📋 Sample Results...")
    print("=" * 50)
    
    # Show email threads
    thread_file = "data/email_threads.json"
    if os.path.exists(thread_file):
        print("📧 Email Threads Sample:")
        with open(thread_file, 'r') as f:
            threads = json.load(f)
        
        if threads:
            thread = threads[0]
            print(f"  Thread ID: {thread['thread_id']}")
            print(f"  Messages: {thread['message_count']}")
            print(f"  Detection: {thread['detection_reasons']}")
            
            if thread['messages']:
                msg = thread['messages'][0]
                print(f"  Subject: {msg['subject']}")
                print(f"  Sender: {msg['sender']}")
    
    # Show parsed JDs
    parsed_file = "data/parsed_jds.json"
    if os.path.exists(parsed_file):
        print("\n📝 Parsed Job Descriptions Sample:")
        with open(parsed_file, 'r') as f:
            parsed_jds = json.load(f)
        
        if parsed_jds:
            jd = parsed_jds[0]
            print(f"  Email ID: {jd['email_id']}")
            print(f"  Subject: {jd['subject']}")
            print(f"  Company: {jd['parsed_data']['company']}")
            print(f"  Role: {jd['parsed_data']['role']}")
            print(f"  Location: {jd['parsed_data']['location']}")
            print(f"  Experience: {jd['parsed_data']['experience_years']} years")
            print(f"  Skills: {len(jd['parsed_data']['skills'])} skills")
    
    # Show export files
    export_dir = Config.get_export_dir()
    if os.path.exists(export_dir):
        print("\n📄 Export Files Sample:")
        files = os.listdir(export_dir)
        for file in files[:2]:  # Show first 2 files
            file_path = os.path.join(export_dir, file)
            if file.endswith('.json'):
                with open(file_path, 'r') as f:
                    content = json.load(f)
                print(f"  {file}: {str(content)[:100]}...")

def main():
    """Run the full pipeline and check results."""
    print("🚀 Running Full Pipeline and Checking Results")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Step 1: Run EmailCollector
    threads, emails = run_email_collection()
    
    # Step 2: Run JDParser
    parsed_jds = run_jd_parsing(emails)
    
    # Step 3: Check database
    check_database_after_pipeline()
    
    # Step 4: Check all storage locations
    check_all_storage_locations()
    
    # Step 5: Show sample results
    show_sample_results()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("📊 Pipeline Results Summary")
    print("=" * 60)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Email Threads: {len(threads) if threads else 0}")
    print(f"Emails: {len(emails) if emails else 0}")
    print(f"Parsed JDs: {len(parsed_jds)}")
    
    print("\n📁 Results Stored In:")
    print("1. Email Threads: data/email_threads.json")
    print("2. Parsed JDs: data/parsed_jds.json")
    print("3. Export Files: data/exports/")
    print("4. Database: ./data/jd_agent.db (if pipeline runs completely)")
    
    print("\n🔍 To inspect results:")
    print("1. View email_threads.json for EmailCollector output")
    print("2. View parsed_jds.json for JDParser output")
    print("3. Check data/exports/ for final question files")
    print("4. Run full pipeline to populate database")

if __name__ == "__main__":
    main()