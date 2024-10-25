import unittest
import os
import tempfile
import shutil
from pathlib import Path
from llmcodeupdater.mapping import update_files, find_file, is_partial_update

class TestMappingModule(unittest.TestCase):
    def setUp(self):
        # Create temporary directory structure
        self.project_root = tempfile.mkdtemp()
        
        # Create nested directory structure
        os.makedirs(os.path.join(self.project_root, 'src/utils'), exist_ok=True)
        os.makedirs(os.path.join(self.project_root, 'src/models'), exist_ok=True)
        os.makedirs(os.path.join(self.project_root, 'tests'), exist_ok=True)
        
        # Create test files
        self.utils_file = os.path.join(self.project_root, 'src/utils/helper.py')
        self.models_file = os.path.join(self.project_root, 'src/models/user.py')
        self.test_file = os.path.join(self.project_root, 'tests/test_helper.py')
        
        # Write initial content
        for file_path in [self.utils_file, self.models_file, self.test_file]:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'# Original content in {os.path.basename(file_path)}')

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.project_root)

    def test_find_file(self):
        # Test finding existing file
        found_path = find_file(self.project_root, 'helper.py')
        self.assertEqual(found_path, self.utils_file)
        
        # Test non-existent file
        not_found = find_file(self.project_root, 'nonexistent.py')
        self.assertEqual(not_found, '')

    def test_is_partial_update(self):
        # Test various partial update indicators
        self.assertTrue(is_partial_update('# rest of code unchanged'))
        self.assertTrue(is_partial_update('// do not change below'))
        self.assertTrue(is_partial_update('/* manual review needed */'))
        self.assertFalse(is_partial_update('def normal_code():\n    pass'))

    def test_successful_update(self):
        updates = [
            ('helper.py', '# Updated helper code'),
            ('user.py', '# Updated user model')
        ]
        
        result = update_files(updates, self.project_root)
        
        self.assertEqual(result['files_updated'], 2)
        self.assertEqual(result['files_skipped'], 0)
        self.assertEqual(len(result['errors']), 0)
        
        # Verify content
        with open(self.utils_file, 'r') as f:
            self.assertEqual(f.read(), '# Updated helper code')
        with open(self.models_file, 'r') as f:
            self.assertEqual(f.read(), '# Updated user model')

    def test_partial_update_handling(self):
        updates = [
            ('helper.py', '# Updated part\n# rest of code unchanged'),
            ('user.py', '# Complete update')
        ]
        
        result = update_files(updates, self.project_root)
        
        self.assertEqual(result['files_updated'], 1)
        self.assertEqual(result['files_skipped'], 1)
        
        # Verify original content preserved for partial update
        with open(self.utils_file, 'r') as f:
            self.assertEqual(f.read(), '# Original content in helper.py')

    def test_missing_file_handling(self):
        updates = [
            ('nonexistent.py', '# Some code'),
            ('helper.py', '# Valid update')
        ]
        
        result = update_files(updates, self.project_root)
        
        self.assertEqual(result['files_updated'], 1)
        self.assertEqual(result['files_skipped'], 1)
        self.assertIn('nonexistent.py', result['unmatched_files'])

    def test_permission_error_handling(self):
        # Make file read-only
        os.chmod(self.utils_file, 0o444)
        
        updates = [('helper.py', '# Try to update')]
        result = update_files(updates, self.project_root)
        
        self.assertEqual(result['files_updated'], 0)
        self.assertEqual(result['files_skipped'], 1)
        self.assertIn('helper.py', result['errors'])
        self.assertIn('Permission denied', result['errors']['helper.py'])

    def test_duplicate_filename_handling(self):
        # Create duplicate file in different directory
        os.makedirs(os.path.join(self.project_root, 'src/other'), exist_ok=True)
        duplicate_file = os.path.join(self.project_root, 'src/other/helper.py')
        with open(duplicate_file, 'w') as f:
            f.write('# Duplicate helper')
            
        updates = [('helper.py', '# Updated content')]
        result = update_files(updates, self.project_root)
        
        # Should update first found instance only
        self.assertEqual(result['files_updated'], 1)
        self.assertEqual(result['files_skipped'], 0)

if __name__ == '__main__':
    unittest.main()