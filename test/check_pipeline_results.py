#!/usr/bin/env python3
"""
Check Pipeline Results

This script helps you understand where EmailCollector and JDParser results are being stored
and examine the current pipeline output.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from jd_agent.components.email_collector import EmailCollector
from jd_agent.components.jd_parser import JDParser
from jd_agent.utils.config import Config
from jd_agent.utils.database import Database

def check_database():
    """Check if database exists and what's in it."""
    print("🗄️  Database Check")
    print("=" * 50)
    
    db_path = Config.DATABASE_PATH
    print(f"Database path: {db_path}")
    
    if os.path.exists(db_path):
        print("✅ Database file exists")
        
        # Connect to database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables found: {[table[0] for table in tables]}")
            
            # Check job_descriptions table
            if ('job_descriptions',) in tables:
                cursor.execute("SELECT COUNT(*) FROM job_descriptions")
                count = cursor.fetchone()[0]
                print(f"Job descriptions in database: {count}")
                
                if count > 0:
                    cursor.execute("SELECT * FROM job_descriptions LIMIT 3")
                    rows = cursor.fetchall()
                    print("\nSample job descriptions:")
                    for i, row in enumerate(rows, 1):
                        print(f"  {i}. ID: {row[0]}, Company: {row[2]}, Role: {row[3]}")
            
            # Check search_results table
            if ('search_results',) in tables:
                cursor.execute("SELECT COUNT(*) FROM search_results")
                count = cursor.fetchone()[0]
                print(f"Search results in database: {count}")
            
            # Check questions table
            if ('questions',) in tables:
                cursor.execute("SELECT COUNT(*) FROM questions")
                count = cursor.fetchone()[0]
                print(f"Questions in database: {count}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
    else:
        print("❌ Database file does not exist")
        print("This means no results have been stored yet.")

def check_exports():
    """Check export files."""
    print("\n📁 Export Files Check")
    print("=" * 50)
    
    export_dir = Config.get_export_dir()
    print(f"Export directory: {export_dir}")
    
    if os.path.exists(export_dir):
        files = os.listdir(export_dir)
        print(f"Export files found: {len(files)}")
        
        for file in files:
            file_path = os.path.join(export_dir, file)
            size = os.path.getsize(file_path)
            print(f"  - {file} ({size} bytes)")
            
            # Show sample content for small files
            if size < 1000 and file.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        content = json.load(f)
                    print(f"    Sample content: {str(content)[:100]}...")
                except:
                    pass
    else:
        print("❌ Export directory does not exist")

def test_email_collector():
    """Test EmailCollector and see what it returns."""
    print("\n📧 EmailCollector Test")
    print("=" * 50)
    
    try:
        collector = EmailCollector()
        
        if not collector.service:
            print("❌ EmailCollector service not available")
            return
        
        print("✅ EmailCollector initialized successfully")
        
        # Test the new thread-based method
        print("\n1. Testing fetch_job_description_threads (last 7 days)...")
        threads = collector.fetch_job_description_threads(days_back=7)
        print(f"Found {len(threads)} job description threads")
        
        if threads:
            print("\nSample thread data:")
            thread = threads[0]
            print(f"  Thread ID: {thread['thread_id']}")
            print(f"  Message Count: {thread['message_count']}")
            print(f"  Detection Reasons: {thread['detection_reasons']}")
            
            if thread['messages']:
                msg = thread['messages'][0]
                print(f"  First Message:")
                print(f"    Subject: {msg['subject']}")
                print(f"    Sender: {msg['sender']}")
                print(f"    Domain Match: {msg['domain_match']}")
                print(f"    Keyword Hit: {msg['keyword_hit']}")
                print(f"    Attachment Hit: {msg['attachment_hit']}")
        
        # Test legacy method
        print("\n2. Testing legacy fetch_jd_emails...")
        emails = collector.fetch_jd_emails(days_back=7)
        print(f"Found {len(emails)} emails")
        
        return threads, emails
        
    except Exception as e:
        print(f"❌ EmailCollector test failed: {e}")
        return None, None

def test_jd_parser(emails):
    """Test JDParser with sample emails."""
    print("\n📝 JDParser Test")
    print("=" * 50)
    
    if not emails:
        print("❌ No emails to parse")
        return
    
    try:
        parser = JDParser()
        print("✅ JDParser initialized successfully")
        
        # Parse first few emails
        parsed_jds = []
        for i, email in enumerate(emails[:3], 1):
            print(f"\nParsing email {i}:")
            print(f"  Subject: {email.get('subject', 'No subject')}")
            
            jd = parser.parse(email)
            if jd:
                print(f"  ✅ Parsed successfully:")
                print(f"    Company: {jd.company}")
                print(f"    Role: {jd.role}")
                print(f"    Location: {jd.location}")
                print(f"    Experience: {jd.experience_years} years")
                print(f"    Skills: {len(jd.skills)} skills")
                parsed_jds.append(jd)
            else:
                print(f"  ❌ Failed to parse")
        
        return parsed_jds
        
    except Exception as e:
        print(f"❌ JDParser test failed: {e}")
        return []

def check_storage_pipeline():
    """Check how results flow through the storage pipeline."""
    print("\n🔄 Storage Pipeline Check")
    print("=" * 50)
    
    # Check if database is being used in the current pipeline
    print("Current storage mechanisms:")
    print("1. Database (SQLite):")
    print("   - Location: ./data/jd_agent.db")
    print("   - Tables: job_descriptions, search_results, questions")
    print("   - Used by: Database class in utils/database.py")
    
    print("\n2. Export Files:")
    print("   - Location: ./data/exports/")
    print("   - Formats: .md, .csv, .json")
    print("   - Used by: QuestionBank class")
    
    print("\n3. Current Pipeline Flow:")
    print("   EmailCollector → JDParser → KnowledgeMiner → PromptEngine → QuestionBank")
    print("   ↓")
    print("   Database (job_descriptions) → Database (search_results) → Database (questions)")
    print("   ↓")
    print("   Export Files (.md, .csv, .json)")
    
    print("\n4. Missing Storage:")
    print("   - EmailCollector results are NOT being stored in database")
    print("   - JDParser results are NOT being stored in database")
    print("   - Only final questions are being stored")

def suggest_improvements():
    """Suggest improvements to the storage pipeline."""
    print("\n💡 Suggested Improvements")
    print("=" * 50)
    
    print("1. Store EmailCollector Results:")
    print("   - Add email_threads table to store thread analysis")
    print("   - Store detection reasons and metadata")
    print("   - Track email processing history")
    
    print("\n2. Store JDParser Results:")
    print("   - Use existing job_descriptions table")
    print("   - Store parsed JD data with email_id reference")
    print("   - Track parsing success/failure rates")
    
    print("\n3. Add Pipeline Tracking:")
    print("   - Add pipeline_runs table to track execution")
    print("   - Store processing timestamps and statistics")
    print("   - Track API usage and costs")
    
    print("\n4. Improve Data Access:")
    print("   - Add methods to query stored results")
    print("   - Create dashboard for pipeline statistics")
    print("   - Add export functionality for stored data")

def main():
    """Run all checks."""
    print("🔍 Pipeline Results Check")
    print("=" * 60)
    
    # Check current storage
    check_database()
    check_exports()
    
    # Test components
    threads, emails = test_email_collector()
    parsed_jds = test_jd_parser(emails)
    
    # Analyze pipeline
    check_storage_pipeline()
    suggest_improvements()
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print("Current Status:")
    print(f"- EmailCollector: Found {len(threads) if threads else 0} threads")
    print(f"- JDParser: Parsed {len(parsed_jds)} job descriptions")
    print(f"- Database: {'Exists' if os.path.exists(Config.DATABASE_PATH) else 'Missing'}")
    print(f"- Exports: {'Available' if os.path.exists(Config.get_export_dir()) else 'Missing'}")
    
    print("\nNext Steps:")
    print("1. Run the full pipeline to generate data")
    print("2. Check database after pipeline execution")
    print("3. Review export files for results")
    print("4. Implement suggested storage improvements")

if __name__ == "__main__":
    main() 