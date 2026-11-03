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
