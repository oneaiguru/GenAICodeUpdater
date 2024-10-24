# tests/test_task_tracking.py

import unittest
import os
import tempfile
import sqlite3
from llmcodeupdater.task_tracking import TaskTracker

class TestTaskTracker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.tracker = TaskTracker(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_add_tasks(self):
        files = ['/path/to/file1.py', '/path/to/file2.py']
        self.tracker.add_tasks(files)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path, status FROM tasks")
            results = cursor.fetchall()
            
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], 'pending')
        self.assertEqual(results[1][1], 'pending')

    def test_update_task_status(self):
        file_path = '/path/to/file1.py'
        self.tracker.add_tasks([file_path])
        self.tracker.update_task_status(file_path, 'updated')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM tasks WHERE file_path = ?", (file_path,))
            status = cursor.fetchone()[0]
            
        self.assertEqual(status, 'updated')

    def test_update_task_status_with_error(self):
        file_path = '/path/to/file1.py'
        self.tracker.add_tasks([file_path])
        error_message = 'Permission denied'
        self.tracker.update_task_status(file_path, 'error', error_message)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, error_message FROM tasks WHERE file_path = ?", (file_path,))
            result = cursor.fetchone()
            
        self.assertEqual(result[0], 'error')
        self.assertEqual(result[1], error_message)

    def test_get_task_summary(self):
        files = ['/path/to/file1.py', '/path/to/file2.py', '/path/to/file3.py']
        self.tracker.add_tasks(files)
        
        self.tracker.update_task_status(files[0], 'updated')
        self.tracker.update_task_status(files[1], 'skipped')
        self.tracker.update_task_status(files[2], 'error', 'Test error')
        
        summary = self.tracker.get_task_summary()
        
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['updated'], 1)
        self.assertEqual(summary['skipped'], 1)
        self.assertEqual(summary['error'], 1)
        self.assertEqual(summary['pending'], 0)
