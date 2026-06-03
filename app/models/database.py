import sqlite3
import os
from typing import Optional
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = "ai_phys.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Gmail emails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                thread_id TEXT,
                subject TEXT,
                sender_email TEXT,
                sender_name TEXT,
                recipient_emails TEXT,
                body_text TEXT,
                body_html TEXT,
                date_sent TIMESTAMP,
                date_received TIMESTAMP,
                labels TEXT,
                message_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Email analysis results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT UNIQUE,
                sentiment_score REAL,
                sentiment_label TEXT,
                keywords TEXT,
                communication_style TEXT,
                urgency_level INTEGER,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_user(self, email: str, name: Optional[str] = None) -> int:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, name) VALUES (?, ?)",
                (email, name)
            )
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            # User already exists, get existing user_id
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, created_at FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'email': result[1],
                'name': result[2],
                'created_at': result[3]
            }
        return None
    
    def store_email(self, email_data: dict) -> bool:
        """Store email data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO emails (
                    id, user_id, thread_id, subject, sender_email, sender_name,
                    recipient_emails, body_text, body_html, date_sent, date_received, labels, message_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_data['id'],
                email_data['user_id'],
                email_data.get('thread_id'),
                email_data.get('subject'),
                email_data.get('sender_email'),
                email_data.get('sender_name'),
                email_data.get('recipient_emails'),
                email_data.get('body_text'),
                email_data.get('body_html'),
                email_data.get('date_sent'),
                email_data.get('date_received'),
                email_data.get('labels'),
                email_data.get('message_type', 'received')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error storing email: {e}")
            return False
        finally:
            conn.close()
    
    def store_analysis(self, email_id: str, analysis_data: dict) -> bool:
        """Store email analysis results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO email_analysis (
                    email_id, sentiment_score, sentiment_label,
                    keywords, communication_style, urgency_level
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                email_id,
                analysis_data.get('sentiment_score'),
                analysis_data.get('sentiment_label'),
                analysis_data.get('keywords'),
                analysis_data.get('communication_style'),
                analysis_data.get('urgency_level'),
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error storing analysis: {e}")
            return False
        finally:
            conn.close()

    def get_email_analysis(self, user_id: int, limit: int = 1000) -> list:
        """Get analysis results for a user's emails"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ea.email_id, ea.sentiment_score, ea.sentiment_label,
                   ea.keywords, ea.communication_style, ea.urgency_level
            FROM email_analysis ea
            JOIN emails e ON ea.email_id = e.id
            WHERE e.user_id = ?
            ORDER BY ea.analyzed_at DESC
            LIMIT ?
        ''', (user_id, limit))
        results = cursor.fetchall()
        conn.close()
        return [
            {
                'email_id': row[0],
                'sentiment_score': row[1],
                'sentiment_label': row[2],
                'keywords': row[3],
                'communication_style': row[4],
                'urgency_level': row[5],
            }
            for row in results
        ]

    def get_user_emails(self, user_id: int, limit: int = 100) -> list:
        """Get emails for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, subject, sender_email, sender_name, date_sent, labels, message_type
            FROM emails 
            WHERE user_id = ? 
            ORDER BY date_sent DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'subject': row[1],
                'sender_email': row[2],
                'sender_name': row[3],
                'date_sent': row[4],
                'labels': row[5],
                'message_type': row[6]
            }
            for row in results
        ]

# Global database instance
db = DatabaseManager()

def init_database():
    """Initialize database (called from main.py)"""
    db.init_database()