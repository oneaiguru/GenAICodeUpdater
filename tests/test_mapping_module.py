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
        self.dirs = {
            'utils': os.path.join(self.project_root, 'src/utils'),
            'services': os.path.join(self.project_root, 'src/services'),
            'models': os.path.join(self.project_root, 'src/models'),
            'tests': os.path.join(self.project_root, 'tests'),
            'analytics': os.path.join(self.project_root, 'src/services/analytics')
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Create test files with nested structure
        self.files = {
            'helper': os.path.join(self.dirs['utils'], 'helper.py'),
            'user': os.path.join(self.dirs['models'], 'user.py'),
            'test_helper': os.path.join(self.dirs['tests'], 'test_helper.py'),
            'analytics': os.path.join(self.dirs['analytics'], 'analytics_service.py'),
            'utils_init': os.path.join(self.dirs['utils'], '__init__.py'),
            'models_init': os.path.join(self.dirs['models'], '__init__.py'),
            'duplicate_helper': os.path.join(self.dirs['services'], 'helper.py')
        }
        
        # Write initial content
        for file_path in self.files.values():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'# Original content in {os.path.basename(file_path)}')

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.project_root)

    def test_find_file_exact_path(self):
        """Test finding file with exact path"""
        rel_path = 'src/services/analytics/analytics_service.py'
        found_path = find_file(self.project_root, rel_path)
        self.assertEqual(found_path, self.files['analytics'])

    def test_find_file_basename_unique(self):
        """Test finding file by basename when unique"""
        found_path = find_file(self.project_root, 'analytics_service.py')
        self.assertEqual(found_path, self.files['analytics'])

    def test_find_file_basename_duplicate(self):
        """Test finding file by basename when duplicate exists"""
        # Should return the first found instance
        found_path = find_file(self.project_root, 'helper.py')
        self.assertTrue(
            found_path in [self.files['helper'], self.files['duplicate_helper']],
            "Should find one of the helper.py files"
        )

    def test_find_file_init(self):
        """Test finding __init__.py files"""
        # Should not match without exact path
        found_path = find_file(self.project_root, '__init__.py')
        self.assertEqual(found_path, "", "Should not match __init__.py without exact path")
        
        # Should match with exact path
        found_path = find_file(self.project_root, 'src/utils/__init__.py')
        self.assertEqual(found_path, self.files['utils_init'])

    def test_update_files_with_exact_paths(self):
        """Test updating files using exact paths"""
        updates = [
            ('src/services/analytics/analytics_service.py', '# Updated analytics service'),
            ('src/models/user.py', '# Updated user model')
        ]
        
        result = update_files(updates, self.project_root)
        
        self.assertEqual(result['files_updated'], 2)
        self.assertEqual(result['files_skipped'], 0)
        
        # Verify content was updated
        with open(self.files['analytics'], 'r') as f:
            self.assertEqual(f.read(), '# Updated analytics service')
        with open(self.files['user'], 'r') as f:
            self.assertEqual(f.read(), '# Updated user model')

    def test_update_files_with_basenames(self):
        """Test updating files using basenames"""
        updates = [
            ('analytics_service.py', '# Updated analytics service'),
            ('user.py', '# Updated user model')
        ]
        
        result = update_files(updates, self.project_root)
        
        self.assertEqual(result['files_updated'], 2)
        self.assertEqual(result['files_skipped'], 0)
        
        # Verify content was updated
        with open(self.files['analytics'], 'r') as f:
            self.assertEqual(f.read(), '# Updated analytics service')
        with open(self.files['user'], 'r') as f:
            self.assertEqual(f.read(), '# Updated user model')

    def test_update_files_with_duplicates(self):
        """Test updating files when duplicates exist"""
        updates = [
            ('helper.py', '# Updated helper')
        ]
        
        result = update_files(updates, self.project_root)
        
        # Should update exactly one instance
        self.assertEqual(result['files_updated'], 1)
        self.assertEqual(result['files_skipped'], 0)
        
        # At least one helper.py should be updated
        updated_content_found = False
        for helper_path in [self.files['helper'], self.files['duplicate_helper']]:
            with open(helper_path, 'r') as f:
                if f.read() == '# Updated helper':
                    updated_content_found = True
                    break
        self.assertTrue(updated_content_found, "No helper.py file was updated")

    def test_update_init_files(self):
        """Test updating __init__.py files"""
        updates = [
            ('__init__.py', '# Updated init'),  # Should not update without exact path
            ('src/utils/__init__.py', '# Updated utils init')  # Should update with exact path
        ]
        
        result = update_files(updates, self.project_root)
        
        self.assertEqual(result['files_updated'], 1)
        self.assertEqual(result['files_skipped'], 1)
        
        # Verify only the exact path match was updated