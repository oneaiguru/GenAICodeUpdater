
import unittest
import os
import tempfile
import shutil
from ValidationModule import compare_files, run_unit_tests, generate_validation_report

class TestValidationModule(unittest.TestCase):

    def setUp(self):
        self.project_root = tempfile.mkdtemp()
        self.backup_root = tempfile.mkdtemp()

        # Create sample original files (backups)
        os.makedirs(os.path.join(self.backup_root, 'utils'), exist_ok=True)
        with open(os.path.join(self.backup_root, 'utils', 'redis_manager.py'), 'w') as f:
            f.write('# Original RedisManager code')

        # Create sample updated files
        os.makedirs(os.path.join(self.project_root, 'utils'), exist_ok=True)
        with open(os.path.join(self.project_root, 'utils', 'redis_manager.py'), 'w') as f:
            f.write('# Updated RedisManager code')

    def tearDown(self):
        shutil.rmtree(self.project_root)
        shutil.rmtree(self.backup_root)

    def test_compare_files(self):
        updated_file = os.path.join(self.project_root, 'utils', 'redis_manager.py')
        backup_file = os.path.join(self.backup_root, 'utils', 'redis_manager.py')
        result = compare_files(updated_file, backup_file)
        self.assertTrue(result)

    def test_run_unit_tests(self):
        result = run_unit_tests(self.project_root)
        self.assertTrue(result['success'])

    def test_generate_report(self):
        comparison_results = [{'file': 'utils/redis_manager.py', 'status': 'modified'}]
        test_results = {'success': True}
        report = generate_validation_report(comparison_results, test_results)
        self.assertIn("utils/redis_manager.py", report)
        self.assertIn("modified", report)
        self.assertIn("All tests passed", report)

if __name__ == '__main__':
    unittest.main()
    