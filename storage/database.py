import sqlite3
import os
import hashlib

class Database:
    def __init__(self, db_path="data/app.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_identifier TEXT NOT NULL,
                    message_hash TEXT NOT NULL,
                    message_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get_setting(self, key, default=""):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO app_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            ''', (key, value))
            conn.commit()

    def get_knowledge_base(self):
        """Returns all documents or snippets in the knowledge base."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, content FROM knowledge_base ORDER BY id DESC')
            return cursor.fetchall()

    def set_knowledge_base(self, content, title="General Info"):
        """Save or replace the main knowledge base text."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM knowledge_base')
            if content.strip():
                cursor.execute('INSERT INTO knowledge_base (title, content) VALUES (?, ?)', (title, content))
            conn.commit()

    def is_message_processed(self, chat_identifier, message_text):
        msg_hash = hashlib.sha256(message_text.encode('utf-8')).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM processed_messages 
                WHERE chat_identifier = ? AND message_hash = ?
            ''', (chat_identifier, msg_hash))
            return cursor.fetchone() is not None

    def mark_message_processed(self, chat_identifier, message_text):
        msg_hash = hashlib.sha256(message_text.encode('utf-8')).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processed_messages (chat_identifier, message_hash, message_text)
                VALUES (?, ?, ?)
            ''', (chat_identifier, msg_hash, message_text))
            conn.commit()
