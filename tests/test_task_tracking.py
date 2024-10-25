# tests/test_task_tracking.py

import unittest
import os
import tempfile
import sqlite3
import time
from datetime import datetime, timedelta
from llmcodeupdater.task_tracking import TaskTracker

class TestTaskTracker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.project_path = "/test/project"
        self.tracker = TaskTracker(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_clear_project_tasks(self):
        """Test clearing tasks for a specific project."""
        # Add tasks for multiple projects
        files1 = ['/path/to/file1.py', '/path/to/file2.py']
        files2 = ['/path/to/file3.py', '/path/to/file4.py']
        self.tracker.add_tasks(files1, "/project1")
        self.tracker.add_tasks(files2, "/project2")
        
        # Clear tasks for project1
        self.tracker.clear_project_tasks("/project1")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Check project1 tasks were cleared
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE created_for_project = ?", ("/project1",))
            self.assertEqual(cursor.fetchone()[0], 0)
            # Check project2 tasks remain
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE created_for_project = ?", ("/project2",))
            self.assertEqual(cursor.fetchone()[0], 2)

    def test_add_tasks_with_project(self):
        """Test adding tasks with project association."""
        files = ['/path/to/file1.py', '/path/to/file2.py']
        self.tracker.add_tasks(files, self.project_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_path, status, created_for_project 
                FROM tasks 
                WHERE created_for_project = ?
            """, (self.project_path,))
            results = cursor.fetchall()
            
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], 'pending')
        self.assertEqual(results[0][2], self.project_path)
        self.assertEqual(results[1][2], self.project_path)

    def test_update_task_status_with_processing_time(self):
        """Test updating task status with processing time tracking."""
        file_path = '/path/to/file1.py'
        processing_time = 1.5
        self.tracker.add_tasks([file_path], self.project_path)
        self.tracker.update_task_status(file_path, 'updated', processing_time=processing_time)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, processing_time FROM tasks WHERE file_path = ?", 
                (file_path,)
            )
            result = cursor.fetchone()
            
        self.assertEqual(result[0], 'updated')
        self.assertEqual(result[1], processing_time)

    def test_get_task_summary_with_performance_metrics(self):
        """Test getting task summary with performance metrics for a project."""
        files = ['/path/to/file1.py', '/path/to/file2.py', '/path/to/file3.py']
        self.tracker.add_tasks(files, self.project_path)
        
        # Update tasks with different statuses and processing times
        self.tracker.update_task_status(files[0], 'updated', processing_time=1.0)
        self.tracker.update_task_status(files[1], 'skipped', processing_time=0.5)
        self.tracker.update_task_status(files[2], 'error', 'Test error', processing_time=2.0)
        
        summary = self.tracker.get_task_summary(self.project_path)
        
        # Check basic counts
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['updated'], 1)
        self.assertEqual(summary['skipped'], 1)
        self.assertEqual(summary['error'], 1)
        self.assertEqual(summary['pending'], 0)
        
        # Check performance metrics
        self.assertIn('performance', summary)
        perf = summary['performance']
        self.assertAlmostEqual(perf['average_processing_time'], (1.0 + 0.5 + 2.0) / 3)
        self.assertAlmostEqual(perf['max_processing_time'], 2.0)
        self.assertAlmostEqual(perf['total_processing_time'], 3.5)

    def test_cleanup_old_tasks(self):
        """Test cleaning up old tasks."""
        # Add some tasks
        files = ['/path/to/file1.py', '/path/to/file2.py']
        self.tracker.add_tasks(files, self.project_path)
        
        # Modify creation date of first task to be old
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            old_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "UPDATE tasks SET created_at = ? WHERE file_path = ?",
                (old_date, files[0])
            )
            conn.commit()
        
        # Run cleanup
        self.tracker.cleanup_old_tasks(days_old=7)
        
        # Check results
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            remaining_tasks = cursor.fetchone()[0]
        
        self.assertEqual(remaining_tasks, 1)
