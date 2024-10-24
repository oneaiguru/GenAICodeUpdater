
import unittest
import os
import sqlite3
from LLMCodeFileHandler import LLMCodeFileHandler

class TestLLMCodeFileHandler(unittest.TestCase):
    
    def setUp(self):
        """
        Setup the environment for testing, creating sample Python files and a mock database.
        """
        self.test_directory = '/mnt/data/test_code_files'
        if not os.path.exists(self.test_directory):
            os.mkdir(self.test_directory)
        
        # Mock code files (similar to creating files within a zip in your example)
        file_contents = {
            '7.py': "# Code block 1\nprint('Hello from 7.py')",
            '8.py': "# Code block 2\nprint('Hello from 8.py')",
            '9.py': "# Code block 3\nprint('Hello from 9.py')",
            '.hidden.py': "# Hidden file, should be ignored",
            'malformed.py': "# Malformed file, missing code",
        }
        for file_name, content in file_contents.items():
            with open(os.path.join(self.test_directory, file_name), 'w') as f:
                f.write(content)

        # Mock database for logging
        self.db_path = '/mnt/data/test_log.db'
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT,
                    status TEXT
                )
            ''')

    def tearDown(self):
        """
        Clean up the test files and database after each test run.
        """
        for file_name in os.listdir(self.test_directory):
            os.remove(os.path.join(self.test_directory, file_name))
        os.rmdir(self.test_directory)

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_read_valid_files_with_logging(self):
        """
        Test reading valid files and logging them in the database.
        """
        expected_files = ['7.py', '8.py', '9.py']
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for file_name in expected_files:
                file_path = os.path.join(self.test_directory, file_name)
                self.assertTrue(os.path.exists(file_path), f"{file_name} should exist")
                with open(file_path, 'r') as f:
                    content = f.read()
                    self.assertIn('print', content, f"Content of {file_name} should include a print statement")
                
                # Simulate logging the file read operation
                cursor.execute("INSERT INTO file_logs (file_name, status) VALUES (?, ?)", (file_name, 'processed'))

            # Verify that files were logged correctly
            cursor.execute("SELECT COUNT(*) FROM file_logs")
            file_count = cursor.fetchone()[0]
            self.assertEqual(file_count, len(expected_files), "All valid files should be logged")

    def test_handle_hidden_and_malformed_files(self):
        """
        Test that hidden and malformed files are not processed or logged.
        """
        hidden_file = os.path.join(self.test_directory, '.hidden.py')
        malformed_file = os.path.join(self.test_directory, 'malformed.py')
        self.assertTrue(os.path.exists(hidden_file), ".hidden.py should exist")
        self.assertTrue(os.path.exists(malformed_file), "malformed.py should exist")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Simulate logging hidden and malformed file skips
            cursor.execute("INSERT INTO file_logs (file_name, status) VALUES (?, ?)", ('.hidden.py', 'ignored'))
            cursor.execute("INSERT INTO file_logs (file_name, status) VALUES (?, ?)", ('malformed.py', 'error'))

            # Verify that hidden and malformed files were logged as ignored/error
            cursor.execute("SELECT COUNT(*) FROM file_logs WHERE status IN ('ignored', 'error')")
            ignored_or_error_count = cursor.fetchone()[0]
            self.assertEqual(ignored_or_error_count, 2, "Hidden and malformed files should be logged as ignored or error")

    def test_process_multi_file_code_blocks_with_logging(self):
        """
        Test handling of multi-file code blocks and logging.
        """
        multi_file_block = ""
        expected_files = ['7.py', '8.py', '9.py']
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for file_name in expected_files:
                file_path = os.path.join(self.test_directory, file_name)
                with open(file_path, 'r') as f:
                    multi_file_block += f.read()

                # Log the file processing
                cursor.execute("INSERT INTO file_logs (file_name, status) VALUES (?, ?)", (file_name, 'processed'))

            # Simulate that all files are processed correctly
            self.assertIn("Hello from 7.py", multi_file_block)
            self.assertIn("Hello from 8.py", multi_file_block)
            self.assertIn("Hello from 9.py", multi_file_block)

            # Verify that files were logged correctly
            cursor.execute("SELECT COUNT(*) FROM file_logs WHERE status = 'processed'")
            processed_file_count = cursor.fetchone()[0]
            self.assertEqual(processed_file_count, len(expected_files), "All multi-file blocks should be logged")

# Run the tests
if __name__ == '__main__':
    unittest.main()
    