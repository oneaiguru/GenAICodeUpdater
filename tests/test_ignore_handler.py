import os
import time
import unittest
from llmcodeupdater.ignore_handler import IgnoreHandler

class TestIgnoreHandler(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        # Create a test .gitignore before initializing handler
        with open(os.path.join(self.test_dir, '.gitignore'), 'w') as f:
            f.write('*.txt\n')
            f.write('temp/\n')
        self.handler = IgnoreHandler(self.test_dir)

    def test_always_ignore_patterns(self):
        """Test that always-ignore patterns are properly loaded."""
        self.assertTrue(self.handler.is_ignored('__pycache__'))
        self.assertTrue(self.handler.is_ignored('test.pyc'))
        self.assertTrue(self.handler.is_ignored('.git'))

    def test_custom_ignore_patterns(self):
        """Test custom ignore patterns."""
        # Create .gitignore has already been created in setUp
        self.assertTrue(self.handler.is_ignored('file.txt'), "Should ignore .txt files")
        self.assertTrue(self.handler.is_ignored('temp/file.py'), "Should ignore files in temp directory")
        self.assertFalse(self.handler.is_ignored('file.py'), "Should not ignore .py files")

    def test_pattern_caching(self):
        """Test that pattern matching uses cache effectively."""
        # First check should cache the result
        start_time = time.time()
        result1 = self.handler.is_ignored('some/long/path/file.pyc')
        first_check_time = time.time() - start_time
        
        # Second check should be faster due to cache
        start_time = time.time()
        result2 = self.handler.is_ignored('some/long/path/file.pyc')
        second_check_time = time.time() - start_time
        
        self.assertEqual(result1, result2)
        self.assertLess(second_check_time, first_check_time)

    def tearDown(self):
        # Clean up test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()