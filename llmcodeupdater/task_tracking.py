# llmcodeupdater/task_tracking.py

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

class TaskTracker:
    def __init__(self, db_path: str):
        """Initialize TaskTracker with database path."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database with required table and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Add created_for_project to track which project tasks belong to
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    file_path TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_for_project TEXT,
                    processing_time REAL DEFAULT 0.0
                )
            """)
            # Add index for faster project-based queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_status 
                ON tasks(created_for_project, status)
            """)
            conn.commit()

    def clear_project_tasks(self, project_path: str) -> None:
        """Clear all tasks for a specific project before starting new run."""
        start_time = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE created_for_project = ?", (project_path,))
            conn.commit()
        logger.info(f"Cleared previous tasks for project {project_path} in {time.time() - start_time:.2f}s")

    def add_tasks(self, file_paths: List[str], project_path: str) -> None:
        """Add new tasks to track with project association."""
        start_time = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Use a single transaction for better performance
            cursor.executemany(
                """INSERT INTO tasks (file_path, created_for_project) 
                   VALUES (?, ?)
                   ON CONFLICT(file_path) DO UPDATE SET 
                   status='pending', 
                   error_message=NULL, 
                   created_for_project=?""",
                [(path, project_path, project_path) for path in file_paths]
            )
            conn.commit()
        logger.info(f"Added {len(file_paths)} tasks for project {project_path} in {time.time() - start_time:.2f}s")
    
    def update_task_status(self, file_path: str, status: str, error_message: Optional[str] = None, processing_time: float = 0.0) -> None:
        """Update the status of a task with processing time."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks 
                SET status = ?, 
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    processing_time = ?
                WHERE file_path = ?
                """,
                (status, error_message, processing_time, file_path)
            )
            conn.commit()
    
    def get_task_summary(self, project_path: str) -> Dict[str, any]:
        """Get a summary of task statuses for specific project with performance metrics."""
        project_path = str(project_path)  # Convert PosixPath to string
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'updated' THEN 1 ELSE 0 END) as updated,
                    SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error,
                    AVG(processing_time) as avg_time,
                    MAX(processing_time) as max_time,
                    SUM(processing_time) as total_time
                FROM tasks
                WHERE created_for_project = ?
            """, (project_path,))
            row = cursor.fetchone()
            
            return {
                'total': row[0],
                'pending': row[1],
                'updated': row[2],
                'skipped': row[3],
                'error': row[4],
                'performance': {
                    'average_processing_time': row[5],
                    'max_processing_time': row[6],
                    'total_processing_time': row[7]
                }
            }

    def cleanup_old_tasks(self, days_old: int = 7) -> None:
        """Clean up tasks older than specified days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """DELETE FROM tasks 
                   WHERE datetime(created_at) < datetime('now', ?)""",
                (f'-{days_old} days',)
            )
            conn.commit()
            