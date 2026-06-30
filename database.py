import os
import sqlite3
from typing import Optional, List, Dict, Any

DB_FILE = "edugenie.db"

def get_connection() -> sqlite3.Connection:
    """
    Establishes and returns a connection to the SQLite database.
    """
    conn = sqlite3.connect(DB_FILE)
    # Enable foreign keys support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db() -> None:
    """
    Initializes the SQLite database schema matching the ERD specifications
    and inserts a default Guest User if not already present.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. USER Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS USER (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. USER_QUERY Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS USER_QUERY (
                query_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query_type TEXT NOT NULL,
                query_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE
            );
        """)
        
        # 3. AI_RESPONSE Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AI_RESPONSE (
                response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL UNIQUE,
                response_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES USER_QUERY(query_id) ON DELETE CASCADE
            );
        """)
        
        # 4. QUIZ Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS QUIZ (
                quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES USER_QUERY(query_id) ON DELETE CASCADE
            );
        """)
        
        # 5. SUMMARY Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SUMMARY (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                original_text TEXT NOT NULL,
                summary_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES USER_QUERY(query_id) ON DELETE CASCADE
            );
        """)
        
        # 6. LEARNING_PATH Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LEARNING_PATH (
                path_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                recommended_resources TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES USER_QUERY(query_id) ON DELETE CASCADE
            );
        """)
        
        # Insert Guest User if empty
        cursor.execute("SELECT user_id FROM USER WHERE user_id = 1;")
        user = cursor.fetchone()
        if not user:
            cursor.execute("""
                INSERT INTO USER (user_id, name, email, password_hash)
                VALUES (1, 'Guest User', 'guest@example.com', 'guest_no_auth');
            """)
        
        conn.commit()

def log_query(user_id: int, query_type: str, query_text: str) -> int:
    """
    Logs the user's incoming query into USER_QUERY table.
    Returns the generated query_id.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO USER_QUERY (user_id, query_type, query_text)
            VALUES (?, ?, ?);
        """, (user_id, query_type, query_text))
        conn.commit()
        return cursor.lastrowid

def log_ai_response(query_id: int, response_text: str, model_used: str) -> int:
    """
    Logs the generated AI response in the AI_RESPONSE table.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO AI_RESPONSE (query_id, response_text, model_used)
            VALUES (?, ?, ?);
        """, (query_id, response_text, model_used))
        conn.commit()
        return cursor.lastrowid

def log_quiz(query_id: int, question_text: str, option_a: str, option_b: str, option_c: str, option_d: str, correct_answer: str) -> int:
    """
    Logs generated quiz question parameters into the QUIZ table.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO QUIZ (query_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (query_id, question_text, option_a, option_b, option_c, option_d, correct_answer))
        conn.commit()
        return cursor.lastrowid

def log_summary(query_id: int, original_text: str, summary_text: str, model_used: str) -> int:
    """
    Logs generated summary details in the SUMMARY table.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SUMMARY (query_id, original_text, summary_text, model_used)
            VALUES (?, ?, ?, ?);
        """, (query_id, original_text, summary_text, model_used))
        conn.commit()
        return cursor.lastrowid

def log_learning_path(query_id: int, topic: str, difficulty_level: str, recommended_resources: str) -> int:
    """
    Logs learning path details in the LEARNING_PATH table.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO LEARNING_PATH (query_id, topic, difficulty_level, recommended_resources)
            VALUES (?, ?, ?, ?);
        """, (query_id, topic, difficulty_level, recommended_resources))
        conn.commit()
        return cursor.lastrowid
