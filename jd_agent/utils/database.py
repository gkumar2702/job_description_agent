"""
Database utilities for JD Agent.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class Database:
    """Database utilities for JD Agent."""
    
    def __init__(self, db_path: str = "./data/jd_agent.db"):
        self.db_path = db_path
        # Expose a connection handle for tests that expect `conn`
        self.conn: Optional[sqlite3.Connection] = None
        self._ensure_data_dir()
        self._create_tables()
        # Maintain a persistent connection only for in-memory DB to preserve tables
        if self.db_path == ":memory:":
            self.conn = sqlite3.connect(self.db_path)
            self._create_tables()
    
    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        conn = self.conn if self.conn else sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Job descriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT UNIQUE,
                    company TEXT,
                    role TEXT,
                    location TEXT,
                    experience TEXT,
                    skills TEXT,
                    confidence_score REAL,
                    parsing_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Search results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT,
                    role TEXT,
                    url TEXT,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    relevance_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Questions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT,
                    role TEXT,
                    question_text TEXT,
                    question_type TEXT,
                    difficulty TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Legacy scrape cache table (kept for compatibility)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_cache (
                    url TEXT PRIMARY KEY,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    content TEXT
                )
            """)

            # Preferred cached_content table expected by tests
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_content (
                    url TEXT PRIMARY KEY,
                    content TEXT,
                    source TEXT,
                    relevance_score REAL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Usage stats table expected by tests
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS usage_stats (key TEXT PRIMARY KEY, value REAL)"
            )
            
            conn.commit()
        finally:
            if not self.conn:
                conn.close()
    
    def insert_job_description(self, email_id: str, company: str, role: str, 
                             location: str, experience: str, skills: list[str], 
                             confidence_score: float, parsing_metadata: dict[str, Any]) -> None:
        """Insert a job description into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO job_descriptions 
                (email_id, company, role, location, experience, skills, confidence_score, parsing_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id, company, role, location, experience, 
                json.dumps(skills), confidence_score, json.dumps(parsing_metadata)
            ))
            conn.commit()
    
    def get_job_description(self, email_id: str) -> Optional[dict[str, Any]]:
        """Get a job description by email ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email_id, company, role, location, experience, skills, 
                       confidence_score, parsing_metadata, created_at
                FROM job_descriptions 
                WHERE email_id = ?
            """, (email_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'email_id': row[0],
                    'company': row[1],
                    'role': row[2],
                    'location': row[3],
                    'experience': row[4],
                    'skills': json.loads(row[5]) if row[5] else [],
                    'confidence_score': row[6],
                    'parsing_metadata': json.loads(row[7]) if row[7] else {},
                    'created_at': row[8]
                }
            return None
    
    def get_all_job_descriptions(self) -> list[dict[str, Any]]:
        """Get all job descriptions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email_id, company, role, location, experience, skills, 
                       confidence_score, parsing_metadata, created_at
                FROM job_descriptions 
                ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            return [
                {
                    'email_id': row[0],
                    'company': row[1],
                    'role': row[2],
                    'location': row[3],
                    'experience': row[4],
                    'skills': json.loads(row[5]) if row[5] else [],
                    'confidence_score': row[6],
                    'parsing_metadata': json.loads(row[7]) if row[7] else {},
                    'created_at': row[8]
                }
                for row in rows
            ]
    
    def insert_search_result(self, company: str, role: str, url: str, 
                           title: str, content: str, source: str, relevance_score: float) -> None:
        """Insert a search result into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_results 
                (company, role, url, title, content, source, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (company, role, url, title, content, source, relevance_score))
            conn.commit()
    
    def get_search_results(self, company: str = "", role: str = "", limit: int = 100) -> list[dict[str, Any]]:
        """Get search results with optional filtering."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT company, role, url, title, content, source, relevance_score, created_at
                FROM search_results
                WHERE 1=1
            """
            params: list[Any] = []
            
            if company:
                query += " AND company LIKE ?"
                params.append(f"%{company}%")
            
            if role:
                query += " AND role LIKE ?"
                params.append(f"%{role}%")
            
            query += " ORDER BY relevance_score DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    'company': row[0],
                    'role': row[1],
                    'url': row[2],
                    'title': row[3],
                    'content': row[4],
                    'source': row[5],
                    'relevance_score': row[6],
                    'created_at': row[7]
                }
                for row in rows
            ]
    
    def insert_question(self, company: str, role: str, question_text: str, 
                       question_type: str, difficulty: str, category: str) -> None:
        """Insert a question into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO questions 
                (company, role, question_text, question_type, difficulty, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (company, role, question_text, question_type, difficulty, category))
            conn.commit()
    
    def get_questions(self, company: str = "", role: str = "", limit: int = 100) -> list[dict[str, Any]]:
        """Get questions with optional filtering."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT company, role, question_text, question_type, difficulty, category, created_at
                FROM questions
                WHERE 1=1
            """
            params: list[Any] = []
            
            if company:
                query += " AND company LIKE ?"
                params.append(f"%{company}%")
            
            if role:
                query += " AND role LIKE ?"
                params.append(f"%{role}%")
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    'company': row[0],
                    'role': row[1],
                    'question_text': row[2],
                    'question_type': row[3],
                    'difficulty': row[4],
                    'category': row[5],
                    'created_at': row[6]
                }
                for row in rows
            ]
    
    def get_cached_content(self, url: str) -> Optional[dict[str, Any]]:
        """Get cached content for a URL if available and not expired."""
        conn = self.conn if self.conn else sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, content, source, relevance_score, fetched_at
                FROM cached_content
                WHERE url = ?
            """, (url,))
            
            row = cursor.fetchone()
            if row:
                url_val, content, source, relevance_score, fetched_at_str = row
                fetched_at = datetime.fromisoformat(fetched_at_str)
                
                # Check if cache is still valid (7 days)
                if datetime.now() - fetched_at < timedelta(days=7):
                    return {
                        'url': url_val,
                        'content': content,
                        'source': source,
                        'relevance_score': relevance_score,
                        'fetched_at': fetched_at_str,
                    }
                else:
                    # Remove expired cache entry
                    cursor.execute("DELETE FROM cached_content WHERE url = ?", (url,))
                    conn.commit()
            
            return None
        finally:
            if not self.conn:
                conn.close()
    
    def cache_content(self, url: str, content: str, source: str | None = None, relevance_score: float | None = None) -> None:
        """Cache content for a URL."""
        conn = self.conn if self.conn else sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cached_content (url, content, source, relevance_score, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (url, content, source, relevance_score, datetime.now().isoformat()))
            conn.commit()
        finally:
            if not self.conn:
                conn.close()
    
    def clear_expired_cache(self) -> int:
        """Clear expired cache entries and return number of cleared entries."""
        conn = self.conn if self.conn else sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM cached_content
                WHERE fetched_at < ?
            """, ((datetime.now() - timedelta(days=7)).isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        finally:
            if not self.conn:
                conn.close()
    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        conn = self.conn if self.conn else sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM cached_content")
            total_entries = cursor.fetchone()[0]
            
            # Valid entries (not expired)
            cursor.execute("""
                SELECT COUNT(*) FROM cached_content
                WHERE fetched_at >= ?
            """, ((datetime.now() - timedelta(days=7)).isoformat(),))
            valid_entries = cursor.fetchone()[0]
            
            # Expired entries
            expired_entries = total_entries - valid_entries
            
            # Calculate hit ratio (this would need to be tracked separately in practice)
            hit_ratio = 0.0  # Placeholder - would need to track actual hits/misses
            
            return {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'hit_ratio': hit_ratio
            }
        finally:
            if not self.conn:
                conn.close()

    # Usage stats helpers expected by tests
    def update_usage_stats(self, key: str, value: float) -> None:
        """Update usage statistic in a simple key-value store."""
        conn = self.conn if self.conn else sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS usage_stats (key TEXT PRIMARY KEY, value REAL)"
            )
            cursor.execute(
                "INSERT INTO usage_stats (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            conn.commit()
        finally:
            if not self.conn:
                conn.close()

    def get_usage_stats(self) -> dict[str, Any]:
        """Retrieve all usage statistics as a dict."""
        conn = self.conn if self.conn else sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS usage_stats (key TEXT PRIMARY KEY, value REAL)")
            cursor.execute("SELECT key, value FROM usage_stats")
            rows = cursor.fetchall()
            return {key: value for key, value in rows}
        finally:
            if not self.conn:
                conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a direct SQLite connection (for testing)."""
        return sqlite3.connect(self.db_path) 