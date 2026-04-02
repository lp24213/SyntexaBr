# -*- coding: utf-8 -*-
import sqlite3
import os
from typing import List, Optional
from datetime import datetime

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "data", "chat_history.db")

def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

def _get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or _DEFAULT_DB
    _ensure_dir(path)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, message TEXT NOT NULL, role TEXT NOT NULL, timestamp REAL NOT NULL)")
    conn.commit()
    return conn

class ChatHistoryDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DEFAULT_DB

    def add(self, user_id: str, message: str, role: str = "user") -> None:
        conn = _get_conn(self.db_path)
        try:
            conn.execute("INSERT INTO chat_history (user_id, message, role, timestamp) VALUES (?, ?, ?, ?)", (user_id, message, role, datetime.utcnow().timestamp()))
            conn.commit()
        finally:
            conn.close()

    def get_recent(self, user_id: str, limit: int = 10) -> List[dict]:
        conn = _get_conn(self.db_path)
        try:
            cur = conn.execute("SELECT message, role, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
            rows = cur.fetchall()
            return [{"message": r[0], "role": r[1], "timestamp": r[2]} for r in reversed(rows)]
        finally:
            conn.close()
