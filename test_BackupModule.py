
import unittest
import tempfile
import os
import shutil
from BackupModule import backup_files

class TestBackupModuleWithErrorHandling(unittest.TestCase):

    def setUp(self):
        self.project_root = tempfile.mkdtemp()
        self.backup_root = tempfile.mkdtemp()

        # Create some sample files
        os.makedirs(os.path.join(self.project_root, 'utils'), exist_ok=True)
        os.makedirs(os.path.join(self.project_root, 'bot'), exist_ok=True)
        
        with open(os.path.join(self.project_root, 'utils', 'redis_manager.py'), 'w') as f:
            f.write('# Original RedisManager code')
        with open(os.path.join(self.project_root, 'bot', 'telegram_bot.py'), 'w') as f:
            f.write('# Original TelegramBot code')
        
        self.file_paths = [
            os.path.join(self.project_root, 'utils', 'redis_manager.py'),
            os.path.join(self.project_root, 'bot', 'telegram_bot.py')
        ]

    def tearDown(self):
        shutil.rmtree(self.project_root)
        shutil.rmtree(self.backup_root)

    def test_backup_files_success(self):
        count = backup_files(self.file_paths, self.project_root, self.backup_root)
        self.assertEqual(count, 2)

        backup_dirs = os.listdir(self.backup_root)
        self.assertEqual(len(backup_dirs), 1)

        backup_timestamp = backup_dirs[0]
        for original_file in self.file_paths:
            relative_path = os.path.relpath(original_file, self.project_root)
            backup_file = os.path.join(self.backup_root, backup_timestamp, relative_path)
            self.assertTrue(os.path.isfile(backup_file))
            with open(backup_file, 'r') as f:
                content = f.read()
                self.assertIn('# Original', content)

    def test_directory_structure_preserved(self):
        count = backup_files(self.file_paths, self.project_root, self.backup_root)
        self.assertEqual(count, 2)

        backup_dirs = os.listdir(self.backup_root)
        backup_timestamp = backup_dirs[0]
        
        expected_paths = [
            os.path.join(self.backup_root, backup_timestamp, 'utils', 'redis_manager.py'),
            os.path.join(self.backup_root, backup_timestamp, 'bot', 'telegram_bot.py')
        ]
        
        for backup_file in expected_paths:
            self.assertTrue(os.path.isfile(backup_file))

    def test_backup_integrity(self):
        count = backup_files(self.file_paths, self.project_root, self.backup_root)
        self.assertEqual(count, 2)

        backup_dirs = os.listdir(self.backup_root)
        backup_timestamp = backup_dirs[0]

        for original_file in self.file_paths:
            relative_path = os.path.relpath(original_file, self.project_root)
            backup_file = os.path.join(self.backup_root, backup_timestamp, relative_path)
            with open(original_file, 'r') as orig_f, open(backup_file, 'r') as backup_f:
                original_content = orig_f.read()
                backup_content = backup_f.read()
                self.assertEqual(original_content, backup_content)

    def test_handle_non_existent_files(self):
        non_existent_file = os.path.join(self.project_root, 'missing_file.py')
        self.file_paths.append(non_existent_file)

        count = backup_files(self.file_paths, self.project_root, self.backup_root)
        self.assertEqual(count, 2)

    def test_cleanup_on_failure(self):
        os.chmod(self.backup_root, 0o400)

        with self.assertRaises(PermissionError):
            backup_files(self.file_paths, self.project_root, self.backup_root)

        backup_dirs = os.listdir(self.backup_root)
        self.assertEqual(len(backup_dirs), 0)

if __name__ == '__main__':
    unittest.main()
    