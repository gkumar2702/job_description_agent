"""
Database utilities for JD Agent.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database manager for JD Agent."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_db_directory()
        self._create_tables()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Job descriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT UNIQUE,
                    company TEXT,
                    role TEXT,
                    location TEXT,
                    experience_years INTEGER,
                    skills TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Search results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jd_id INTEGER,
                    source TEXT,
                    url TEXT,
                    title TEXT,
                    snippet TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (jd_id) REFERENCES job_descriptions (id)
                )
            """)
            
            # Questions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jd_id INTEGER,
                    difficulty TEXT,
                    question TEXT,
                    answer TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (jd_id) REFERENCES job_descriptions (id)
                )
            """)
            
            conn.commit()
            logger.info("Database tables created successfully")
    
    def insert_job_description(self, email_id: str, company: str, role: str, 
                             location: str, experience_years: int, 
                             skills: List[str], content: str) -> int:
        """
        Insert a job description into the database.
        
        Args:
            email_id: Email ID
            company: Company name
            role: Job role
            location: Job location
            experience_years: Years of experience required
            skills: List of required skills
            content: Full job description content
            
        Returns:
            int: ID of the inserted job description
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if job description already exists
            cursor.execute("SELECT id FROM job_descriptions WHERE email_id = ?", (email_id,))
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"Job description for email {email_id} already exists")
                return existing[0]
            
            cursor.execute("""
                INSERT INTO job_descriptions 
                (email_id, company, role, location, experience_years, skills, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (email_id, company, role, location, experience_years, 
                  ','.join(skills), content))
            
            jd_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Inserted job description with ID: {jd_id}")
            return jd_id
    
    def insert_search_results(self, jd_id: int, results: List[Dict[str, Any]]) -> None:
        """
        Insert search results into the database.
        
        Args:
            jd_id: Job description ID
            results: List of search result dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for result in results:
                cursor.execute("""
                    INSERT INTO search_results 
                    (jd_id, source, url, title, snippet, content)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (jd_id, result.get('source'), result.get('url'), 
                      result.get('title'), result.get('snippet'), 
                      result.get('content')))
            
            conn.commit()
            logger.info(f"Inserted {len(results)} search results for JD ID: {jd_id}")
    
    def insert_questions(self, jd_id: int, questions: List[Dict[str, Any]]) -> None:
        """
        Insert generated questions into the database.
        
        Args:
            jd_id: Job description ID
            questions: List of question dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for question in questions:
                cursor.execute("""
                    INSERT INTO questions 
                    (jd_id, difficulty, question, answer, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (jd_id, question.get('difficulty'), question.get('question'),
                      question.get('answer'), question.get('source')))
            
            conn.commit()
            logger.info(f"Inserted {len(questions)} questions for JD ID: {jd_id}")
    
    def get_job_description(self, jd_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a job description by ID.
        
        Args:
            jd_id: Job description ID
            
        Returns:
            Optional[Dict[str, Any]]: Job description data or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM job_descriptions WHERE id = ?
            """, (jd_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'email_id': row[1],
                    'company': row[2],
                    'role': row[3],
                    'location': row[4],
                    'experience_years': row[5],
                    'skills': row[6].split(',') if row[6] else [],
                    'content': row[7],
                    'created_at': row[8]
                }
            return None
    
    def get_search_results(self, jd_id: int) -> List[Dict[str, Any]]:
        """
        Get search results for a job description.
        
        Args:
            jd_id: Job description ID
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM search_results WHERE jd_id = ?
            """, (jd_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'jd_id': row[1],
                    'source': row[2],
                    'url': row[3],
                    'title': row[4],
                    'snippet': row[5],
                    'content': row[6],
                    'created_at': row[7]
                }
                for row in rows
            ]
    
    def get_questions(self, jd_id: int) -> List[Dict[str, Any]]:
        """
        Get questions for a job description.
        
        Args:
            jd_id: Job description ID
            
        Returns:
            List[Dict[str, Any]]: List of questions
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM questions WHERE jd_id = ? ORDER BY difficulty
            """, (jd_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'jd_id': row[1],
                    'difficulty': row[2],
                    'question': row[3],
                    'answer': row[4],
                    'source': row[5],
                    'created_at': row[6]
                }
                for row in rows
            ]
    
    def get_all_job_descriptions(self) -> List[Dict[str, Any]]:
        """
        Get all job descriptions.
        
        Returns:
            List[Dict[str, Any]]: List of all job descriptions
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM job_descriptions ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'email_id': row[1],
                    'company': row[2],
                    'role': row[3],
                    'location': row[4],
                    'experience_years': row[5],
                    'skills': row[6].split(',') if row[6] else [],
                    'content': row[7],
                    'created_at': row[8]
                }
                for row in rows
            ] 