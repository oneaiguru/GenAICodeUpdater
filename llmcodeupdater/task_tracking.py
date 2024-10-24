# llmcodeupdater/task_tracking.py

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

class TaskTracker:
    def __init__(self, db_path: str):
        """Initialize TaskTracker with database path."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database with required table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    file_path TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_tasks(self, file_paths: List[str]) -> None:
        """Add new tasks to track."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO tasks (file_path) VALUES (?)",
                [(path,) for path in file_paths]
            )
            conn.commit()
    
    def update_task_status(self, file_path: str, status: str, error_message: Optional[str] = None) -> None:
        """Update the status of a task."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks 
                SET status = ?, 
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP 
                WHERE file_path = ?
                """,
                (status, error_message, file_path)
            )
            conn.commit()
    
    def get_task_summary(self) -> Dict[str, int]:
        """Get a summary of task statuses."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'updated' THEN 1 ELSE 0 END) as updated,
                    SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error
                FROM tasks
            """)
            row = cursor.fetchone()
            
            return {
                'total': row[0],
                'pending': row[1],
                'updated': row[2],
                'skipped': row[3],
                'error': row[4]
            }
